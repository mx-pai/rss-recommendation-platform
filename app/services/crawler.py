import asyncio
from playwright.async_api import async_playwright
import feedparser
from bs4 import BeautifulSoup
import feedparser
from typing import Dict, Optional, List
from datetime import datetime
import logging
import json
from urllib.parse import urlparse


logger = logging.getLogger(__name__)

class ModernWebCrawler:
    """网页内容抓取器 --使用PlayWeight"""

    def __init__(self, headless: bool = True, timeout: int = 30000):
        self.timeout = timeout
        self.headless = headless

    
    async def crawl_webpage(self, url: str, config: Optional[Dict] = None) -> Optional[Dict]:
        """异步抓取网页内容"""
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                        headless=self.headless,
                        args=['--no-sandbox', '--disable-dev-shm-usage']
                        )
                page = await browser.new_page()

                await page.set_viewport_size({"width": 1920, "height": 1080})
                await page.set_extra_http_headers({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                    })

                await page.goto(url, wait_until='networkidle', timeout=self.timeout)

                await page.wait_for_load_state('domcontentloaded')

                await self._wait_for_content(page, config)

                article_data = await self._extract_article_data(page, url, config)

                await browser.close()
                return article_data
        except Exception as e:
            logger.error(f"抓取网页失败{url}:{str(e)}")

    async def _wait_for_content(self, page, config: Optional[Dict] = None):
        """加载内容"""
        try:
            await page.wait_for_selector('h1, .title, .article-title, .post-title', timeout=10000)
            await page.wait_for_selector('article, .content, .post-content, .article-content', timeout=10000)
        except Exception as e:
            logger.warning(f"等待内容超时：{str(e)}")

    async def _extract_article_data(self, page, url: str, config: Optional[Dict] = None) -> Dict:
        """提取文章数据"""
        try:
            title = await self._extract_title(page, config)

            content = await self._extract_content(page, config)

            author = await self._extract_author(page, config)

            published_at = await self._extract_publish_date(page, config)

            images = await self._extract_images(page, config)

            summary = self._generate_summary(content)

            return {
                    'title': title,
                    'content': content,
                    'author': author,
                    'published_at': published_at,
                    'url': url,
                    'images': images,
                    'domain': urlparse(url).netloc,
                    'summary': summary
                    }
        except Exception as e:
            logger.error(f"提取文章内容失败：{str(e)}")
            return {}

    def _generate_summary(self, content: str) -> str:
        """生成文章摘要（暂时pass，后续用LLM优化）"""
        return ""

    async def _extract_title(self, page, config: Optional[Dict] = None) -> str:
        """提取标题"""
        title_selectors = [
            'h1',
            'meta[property="og:title"]',
            'meta[name="twitter:title"]',
            '.article-title',
            '.post-title',
            '.entry-title',
            '.headline',
            'title'
        ]

        for selector in title_selectors:
            try:
                if selector.startswith('meta'):
                    element = await page.query_selector(selector)
                    if element:
                        title = await element.get_attribute('content')
                        if title and title.strip():
                            return title.strip()
                else:
                    element = await page.query_selector(selector)
                    if element:
                        title = await element.text_content()
                        if title and title.strip():
                            return title.strip()
            except:
                continue

        return "无标题"

    async def _extract_content(self, page, config: Optional[Dict] = None) -> str:
        """提取内容"""
        content_selectors = [
            'article',
            '.article-content',
            '.post-content',
            '.entry-content',
            '.content',
            '.post',
            '.story-content',
            '.main-content'
        ]

        for selector in content_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    await page.evaluate("""
                                        (element) => {
                                            const selectors = ['script', 'style', 'nav', '.advertisement', '.sidebar', '.comments'];
                                            selectors.forEach(sel => {
                                                const elements = elements.querySelectorAll(sel);
                                                elements.forEach(el => sl.remove());
                                                });
                                            }
                                        """, element)
                    content = await element.text_content()
                    if content and len(content.strip()) > 100:
                        return content.strip()
            except:
                continue
        return ""

    async def _extract_author(self, page, config: Optional[Dict] = None) -> str:
        """提取作者"""
        author_selectors = [
            '.author',
            '.byline',
            '.post-author',
            '.article-author',
            'meta[name="author"]',
            'meta[property="article:author"]'
        ]

        for selector in author_selectors:
            try:
                if selector.startswith('meta'):
                    element = await page.query_selector(selector)
                    if element:
                        author = await element.get_attribute('content')
                        if author and author.atrip():
                            return author.strip()
                else:
                    element = await page.query_selector(selector)
                    if element:
                        author = await page.text_content()
                        if author and author.strip():
                            return author.strip()

            except:
                continue

        return "未知作者"


    async def _extract_publish_date(self, page, config: Optional[Dict] = None) -> Optional[datetime]:
        """提取发布时间"""
        date_selectors = [
            'meta[property="article:published_time"]',
            'meta[name="publish_date"]',
            'time',
            '.publish-date',
            '.post-date',
            '.article-date',
            '.entry-date'
        ]
        for selector in date_selectors:
            try:
                if selector.startswith('meta'):
                    element = await page.query_selector(selector)
                    if element:
                        date_str = await element.get_attribute('content')
                        if date_str:
                            return self._parse_date(date_str)
                else:
                    element = await page.query_selector(selector)
                    if element:
                        date_str = await element.text_content()
                        if date_str:
                            return self._parse_date(date_str)
            except:
                continue
        
        return None

    async def _extract_images(self, page, config: Optional[Dict] = None) -> List[str]:
        """提取文章图片"""
        try:
            images = await page.query_selector_all('article img, .content img, .post-content img')
            imgae_urls = []

            for img in images:
                src = await img.get_attribute('src')
                if src and not src.startswith('data:'):
                    imgae_urls.append(src)
            return imgae_urls[:5]

        except:
            return []

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """解析日期字符串"""
        try:
            from dateutil import parser
            return parser.parse(date_str)
        except:
            return None

class RSSCrawler:
    """RSS内容抓取器"""
    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    def crawl_rss(self, rss_url: str) -> List[Dict]: 
        """抓取RSS内容"""
        try:
            feed = feedparser.parse(rss_url)
            
            articles = []
            for entry in feed.entries:
                link = entry.get('link', '')
                if isinstance(link, list) and link:
                    if isinstance(link[0], dict):
                        link = link[0].get('herf','')   
                    else:
                        link = str(link[0])
                elif not isinstance(link, str):
                    link = str(link) if link else ''

                article_data = {
                        'title': entry.get('title', '无标题'),
                        'content': entry.get('summary', ''),
                        'url': link,
                        'author': entry.get('author', '未知作者'),
                        'published_at': self._parse_date(entry.get('published', '')), #type: ignore
                        'domain': urlparse(link).netloc if link else '' #type: ignore
                        }
                articles.append(article_data)

            return articles
        
        except Exception as e:
            logger.error(f"抓取RSS失败{rss_url}: {str(e)}")
            return []

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """"解析RSS日期"""
        try:
            from dateutil import parser
            return parser.parse(date_str)
        except:
            return None

