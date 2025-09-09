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
import bleach
import re
from app.services.ai_service import AIService

logger = logging.getLogger(__name__)

ALLOWED_TAGS = bleach.sanitizer.ALLOWED_TAGS.union({
    "p","br","h1","h2","h3","h4","h5","h6","ul","ol","li","strong","em","blockquote","pre","code","img","a","hr"
    })
ALLOWED_ATTRS = {
    **bleach.sanitizer.ALLOWED_ATTRIBUTES,
    "img": ["str", "alt", "title"],
    "a": ["herf", "title", "rel", "target"]
        }



class ModernWebCrawler:
    """网页内容抓取器 --使用PlayWeight"""

    def __init__(self, headless: bool = True, timeout: int = 30000):
        self.timeout = timeout
        self.headless = headless
        self.ai_service = AIService()


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

            await page.wait_for_load_state('domcontentloaded', timeout=5000)
            logger.info("页面DOM加载完成")

            title_selectors = [
                'h1', '.title', '.article-title', '.post-title',
                '.main h1', '#content h1', '.container h1',
                'h1, h2, h3'
            ]

            content_selectors = [
                'article', '.content', '.post-content', '.article-content',
                '.main', '#content', '.container', '.wrapper',
                '.tutorial-content', '.code-example', '.example',
                'main', 'section', 'div', 'p'
            ]

            for selector in title_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=2000)
                    logger.info(f"找到标题选择器: {selector}")
                    break
                except:
                    continue

            # 尝试找到内容
            for selector in content_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=2000)
                    logger.info(f"找到内容选择器: {selector}")
                    break
                except:
                    continue

            logger.warning("未找到任何内容选择器，但继续尝试提取")

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

            summary = await self.ai_service.generate_summary(
                    content=content,
                    max_length=500
                    )

            category = await self.ai_service.classify_article(
                    title=title,
                    content=content
                    )

            keyword = await self.ai_service.extract_keywords(
                    content=content,
                    max_keywords=5
                    )

            return {
                    'title': title,
                    'content': content,
                    'author': author or '未知作者',
                    'keyword': keyword,
                    'category': category,
                    'published_at': published_at,
                    'url': url,
                    'images': images,
                    'domain': urlparse(url).netloc,
                    'summary': summary
                    }
        except Exception as e:
            logger.error(f"提取文章内容失败：{str(e)}")
            return {}

    async def _generate_summary(self, content: str) -> str:
        """AI生成文章摘要"""
        try:
            # 直接调用AI服务
            ai_summary = await self.ai_service.generate_summary(content, max_length=500)
            if ai_summary:
                logger.info(f"AI摘要生成成功，长度: {len(ai_summary)}")
                return ai_summary
            else:
                logger.warning("AI摘要生成失败，使用基础摘要")
                return self._generate_fallback_summary(content, max_length=150)

        except Exception as e:
            logger.warning(f"AI摘要生成失败: {str(e)}，使用基础摘要")
            return self._generate_fallback_summary(content, max_length=150)

    def _generate_fallback_summary(self, content: str, max_length: int = 150) -> str:
        """基础摘要（备用方案）"""
        if not content:
            return ""

        try:
            soup = BeautifulSoup(content, 'html.parser')
            text = soup.get_text(separator=' ', strip=True)

            if len(text) <= max_length:
                return text

            truncated = text[:max_length]
            last_period = truncated.rfind('。')
            if last_period > max_length * 0.7:
                return truncated[:last_period + 1]
            else:
                return truncated + "..."

        except Exception as e:
            logger.error(f"基础摘要生成失败: {str(e)}")
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
            '.main-content',
            '.post',
            '.entry',
            '.blog-post',
            '.blog-entry',
            '.post-text',
            '.entry-text',
            '.post-body',
            '.entry-body'
        ]


        for selector in content_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    await page.evaluate("""
                                        (element) => {
                                            const selectors = ['script', 'style', 'nav', '.advertisement', '.sidebar', '.comments'];
                                            selectors.forEach(sel => {
                                                const elements = element.querySelectorAll(sel);
                                                elements.forEach(el => el.remove());
                                                });
                                            }
                                        """, element)
                    content = await element.text_content()

                    if content and len(content.strip()) > 100:
                        return content.strip()
                    else:
                        logger.warning(f"⚠️ 选择器 {selector} 的内容太短，长度: {len(content.strip()) if content else 0}")
            except:
                continue
        return ""

    async def _extract_author(self, page, config: Optional[Dict] = None) -> Optional[str]:
        """提取作者信息 - 从多个位置寻找"""
        try:
            # 1. 先尝试从meta标签获取作者
            meta_selectors = [
                'meta[name="author"]',
                'meta[property="article:author"]',
                'meta[property="og:author"]',
                'meta[name="twitter:creator"]'
            ]

            for selector in meta_selectors:
                element = await page.query_selector(selector)
                if element:
                    author = await element.get_attribute('content')
                    if author and author.strip():
                        logger.info(f"从meta标签找到作者: {author}")
                        return author.strip()

            # 2. 从页面元素获取作者
            author_selectors = [
                '.author',
                '.byline',
                '.post-author',
                '.article-author',
                '.entry-author',
                '[rel="author"]',
                '.author-name',
                '.writer',
                '.contributor',
                'dc:creator'
            ]

            for selector in author_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        author_text = await element.text_content()
                        if author_text and author_text.strip():
                            # 清理作者文本
                            cleaned_author = self._clean_author_text(author_text.strip())
                            if cleaned_author:
                                logger.info(f"从页面元素找到作者: {cleaned_author}")
                                return cleaned_author
                except:
                    continue

            # 3. 尝试从JavaScript获取作者信息
            try:
                author_from_js = await page.evaluate(r"""
                    () => {
                        // 尝试从各种可能的JavaScript变量中获取作者
                        if (window.author) return window.author;
                        if (window.articleAuthor) return window.articleAuthor;
                        if (window.postAuthor) return window.postAuthor;
                        return null;
                    }
                """)
                if author_from_js:
                    logger.info(f"从JavaScript找到作者: {author_from_js}")
                    return author_from_js
            except:
                pass

            logger.warning("未找到作者信息")
            return None

        except Exception as e:
            logger.error(f"提取作者失败: {str(e)}")
            return None

    async def _extract_meta_author(self, page) -> Optional[str]:
        """从meta标签找到作者"""
        try:
            meta_selectors = [
                    'meta[name="author"]',
                    'meta[property="article:author"]',
                    'meta[property="og:author"]',
                    'meta[name="twitter:creator"]',
                    'meta[property="author"]',
                    'meta[name="creator"]',
                    'meta[name="writer"]'
                    ]
            for selector in meta_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        author = await element.get_attribute('content')
                        if author and author.strip():
                            cleaned_author = self._clean_author_text(author.strip())
                            if cleaned_author:
                                logger.info(f"从meta标签找到作者：{cleaned_author}")
                                return cleaned_author
                except Exception as e:
                    logger.debug(f"meta选择器{selector}失败：{str(e)}")
                    continue
            return None
        except Exception as e:
            logger.debug(f"提取meta作者失败：{str(e)}")
            return None

    async def _extract_page_author(self, page) -> Optional[str]:
        """从页面元素找到作者"""
        try:
            author_selectors = [
                    '.author',
                    '.byline',
                    '.post-author',
                    '.article-author',
                    '.entry-author',
                    '[rel="author"]',
                    '.author-name',
                    '.writer',
                    '.contributor',
                    '.post-meta .author',
                    '.entry-meta .author',
                    '.article-meta .author',
                    '.post-info .author',
                    '.entry-info .author',
                    '.meta .author',
                    '.info .author'
                    ]
            for selector in author_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        author_text = await element.text_content()
                        if author_text and author_text.strip():
                            cleaned_author = self._clean_author_text(author_text.strip())
                            if cleaned_author:
                                logger.info(f"✅ 从页面元素找到作者: {cleaned_author}")
                                return cleaned_author
                except Exception as e:
                    logger.debug(f"作者选择器 {selector} 失败: {str(e)}")
                    continue
            return None
        except Exception as e:
            logger.debug(f"提取页面作者失败: {str(e)}")
            return None


    async def _extract_title_author(self, page) -> Optional[str]:
        """从标题附近提取作者"""
        try:
            title_element = await page.query_selector('h1, .title, .article-title, .post-title, .entry-title')
            if title_element:
                # 使用JavaScript查找标题附近的作者信息
                author_near_title = await page.evaluate("""
                    (titleElement) => {
                        // 查找标题前后的兄弟元素
                        let prev = titleElement.previousElementSibling;
                        let next = titleElement.nextElementSibling;

                        // 检查前一个元素
                        if (prev) {
                            let authorEl = prev.querySelector('.author, .byline, [rel="author"], .post-author, .article-author, .meta, .info');
                            if (authorEl) return authorEl.textContent.trim();
                        }

                        // 检查后一个元素
                        if (next) {
                            let authorEl = next.querySelector('.author, .byline, [rel="author"], .post-author, .article-author, .meta, .info');
                            if (authorEl) return authorEl.textContent.trim();
                        }

                        // 查找标题父元素中的作者信息
                        let parent = titleElement.parentElement;
                        if (parent) {
                            let authorEl = parent.querySelector('.author, .byline, [rel="author"], .post-author, .article-author, .meta, .info');
                            if (authorEl) return authorEl.textContent.trim();

                            // 查找父元素中的meta信息
                            let metaEl = parent.querySelector('.meta, .info, .post-meta, .entry-meta');
                            if (metaEl) {
                                let authorInMeta = metaEl.querySelector('.author, .byline');
                                if (authorInMeta) return authorInMeta.textContent.trim();
                            }
                        }

                        return null;
                    }
                """, title_element)

                if author_near_title:
                    cleaned_author = self._clean_author_text(author_near_title)
                    if cleaned_author:
                        logger.info(f"✅ 从标题附近找到作者: {cleaned_author}")
                        return cleaned_author
            return None
        except Exception as e:
            logger.debug(f"提取标题作者失败: {str(e)}")
            return None

    async def _extract_attribute_author(self, page) -> Optional[str]:
        """从特殊属性提取作者"""
        try:
            # 查找带有author相关属性的元素
            author_attr_selectors = [
                '[title*="author"]',
                '[title*="Author"]',
                '[data-author]',
                '[data-writer]',
                '[data-creator]'
            ]

            for selector in author_attr_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    for element in elements:
                        # 检查title属性
                        title_attr = await element.get_attribute('title')
                        if title_attr:
                            author_from_title = self._extract_author_from_title(title_attr)
                            if author_from_title:
                                logger.info(f"✅ 从title属性找到作者: {author_from_title}")
                                return author_from_title

                        # 检查data属性
                        data_author = await element.get_attribute('data-author')
                        if data_author:
                            cleaned_author = self._clean_author_text(data_author.strip())
                            if cleaned_author:
                                logger.info(f"✅ 从data-author属性找到作者: {cleaned_author}")
                                return cleaned_author

                except Exception as e:
                    logger.debug(f"属性选择器 {selector} 失败: {str(e)}")
                continue
            return None
        except Exception as e:
            logger.debug(f"提取属性作者失败: {str(e)}")
            return None

    async def _extract_js_author(self, page) -> Optional[str]:
        """使用JavaScript深度搜索作者"""
        try:
            author_from_js = await page.evaluate("""
                () => {
                    // 1. 查找所有可能包含作者信息的元素
                    const possibleAuthors = [];

                    // 查找带有特定class的元素
                    const authorClasses = ['.author', '.byline', '.post-author', '.article-author', '.entry-author'];
                    authorClasses.forEach(cls => {
                        const elements = document.querySelectorAll(cls);
                        elements.forEach(el => {
                            if (el.textContent.trim()) {
                                possibleAuthors.push(el.textContent.trim());
                            }
                        });
                    });

                    // 查找带有特定属性的元素
                    const authorAttrs = ['[title*="author"]', '[title*="Author"]', '[data-author]'];
                    authorAttrs.forEach(attr => {
                        const elements = document.querySelectorAll(attr);
                        elements.forEach(el => {
                            const title = el.getAttribute('title');
                            if (title && title.toLowerCase().includes('author')) {
                                if (title.includes(':')) {
                                    const authorName = title.split(':')[1].trim();
                                    if (authorName) possibleAuthors.push(authorName);
                                } else {
                                    possibleAuthors.push(title);
                                }
                            }

                            const dataAuthor = el.getAttribute('data-author');
                            if (dataAuthor) possibleAuthors.push(dataAuthor);
                        });
                    });

                    // 查找页面中任何包含"作者"、"by"等关键词的文本
                    const walker = document.createTreeWalker(
                        document.body,
                        NodeFilter.SHOW_TEXT,
                        null,
                        false
                    );

                    let node;
                    while (node = walker.nextNode()) {
                        const text = node.textContent.trim();
                        if (text.length > 0 && text.length < 100) {
                            if (text.includes('作者') || text.includes('by') || text.includes('撰稿') || text.includes('编辑')) {
                                possibleAuthors.push(text);
                            }
                        }
                    }

                    // 返回第一个有效的作者信息
                    for (const author of possibleAuthors) {
                        if (author && author.length > 1 && author.length < 50) {
                            // 清理文本
                            let cleaned = author.replace(/^作者[：:]\s*/, '')
                                            .replace(/^by\s+/i, '')
                                            .replace(/^撰稿[：:]\s*/, '')
                                            .replace(/^编辑[：:]\s*/, '')
                                            .trim();
                            if (cleaned.length > 1) {
                                return cleaned;
                            }
                        }
                    }

                    return null;
                }
            """)

            if author_from_js:
                cleaned_author = self._clean_author_text(author_from_js)
                if cleaned_author:
                    logger.info(f"✅ 从JavaScript找到作者: {cleaned_author}")
                    return cleaned_author
            return None
        except Exception as e:
            logger.debug(f"JavaScript搜索作者失败: {str(e)}")
            return None

    async def _extract_keyword_author(self, page) -> Optional[str]:
        """关键词搜索作者"""
        try:
            # 获取页面所有文本
            page_text = await page.text_content()
            if page_text:
                # 定义作者相关的关键词模式
                author_patterns = [
                    r'作者[：:]\s*([^\n\r]+)',
                    r'by\s+([^\n\r]+)',
                    r'撰稿[：:]\s*([^\n\r]+)',
                    r'编辑[：:]\s*([^\n\r]+)',
                    r'发布者[：:]\s*([^\n\r]+)',
                    r'writer[：:]\s*([^\n\r]+)',
                    r'author[：:]\s*([^\n\r]+)'
                ]

                for pattern in author_patterns:
                    match = re.search(pattern, page_text, re.IGNORECASE)
                    if match:
                        author_text = match.group(1).strip()
                        cleaned_author = self._clean_author_text(author_text)
                        if cleaned_author and len(cleaned_author) > 2:
                            logger.info(f"✅ 从关键词模式找到作者: {cleaned_author}")
                            return cleaned_author
            return None
        except Exception as e:
            logger.debug(f"关键词搜索作者失败: {str(e)}")
            return None

    def _extract_author_from_title(self, title: str) -> Optional[str]:
        """从title属性中提取作者名"""
        try:
            if not title:
                return None

            # 处理 "Author: DIYgod" 格式
            if 'author:' in title.lower():
                author_name = title.split(':', 1)[1].strip()
                if author_name:
                    return self._clean_author_text(author_name)

            # 处理 "by DIYgod" 格式
            if title.lower().startswith('by '):
                author_name = title[3:].strip()
                if author_name:
                    return self._clean_author_text(author_name)

            # 如果title包含author但没有冒号
            if 'author' in title.lower():
                author_name = title.replace('Author', '').replace('author', '').strip()
                if author_name and len(author_name) > 1:
                    return self._clean_author_text(author_name)

            return None
        except Exception as e:
            logger.debug(f"从title提取作者失败: {str(e)}")
            return None

    def _clean_author_text(self, author_text: str) -> str:
        """清理作者文本，去除多余信息"""
        if not author_text:
            return ""

        # 去除常见的无关文本
        author_text = re.sub(r'^by\s+', '', author_text, flags=re.IGNORECASE)
        author_text = re.sub(r'^作者[:：]\s*', '', author_text)
        author_text = re.sub(r'^撰稿[:：]\s*', '', author_text)
        author_text = re.sub(r'^编辑[:：]\s*', '', author_text)
        author_text = re.sub(r'^发布者[:：]\s*', '', author_text)

        # 去除日期、时间等无关信息
        author_text = re.sub(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}', '', author_text)
        author_text = re.sub(r'\d{1,2}:\d{1,2}', '', author_text)

        # 去除HTML标签
        author_text = re.sub(r'<[^>]+>', '', author_text)

        # 清理空白字符
        author_text = re.sub(r'\s+', ' ', author_text).strip()

        # 如果清理后太短，返回原文本
        if len(author_text) < 2:
            return author_text

        return author_text




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
        """提取图片"""
        images = []
        try:
            # 1. 优先获取OG图片和Twitter图片
            og_image = await page.query_selector('meta[property="og:image"]')
            if og_image:
                og_src = await og_image.get_attribute('content')
                if og_src and not og_src.startswith('data:'):
                    images.append(og_src)

            twitter_image = await page.query_selector('meta[name="twitter:image"]')
            if twitter_image:
                twitter_src = await twitter_image.get_attribute('content')
                if twitter_src and not twitter_src.startswith('data:') and twitter_src not in images:
                    images.append(twitter_src)

            # 2. 从内容中提取图片
            content_images = await page.query_selector_all('article img, .content img, .post-content img, .article-content img')
            for img in content_images:
                src = await img.get_attribute('src')
                if src and not src.startswith('data:') and src not in images:
                    try:
                        width = await img.get_attribute('width')
                        height = await img.get_attribute('height')
                        if width and height:
                            w, h = int(width), int(height)
                            if w > 200 and h > 200:  # 只选择足够大的图片
                                images.append(src)
                        else:
                            images.append(src)
                    except:
                        images.append(src)

                if len(images) >= 10:  # 限制图片数量
                    break

            # 3. 如果没有找到图片，尝试备用选择器
            if not images:
                fallback_images = await page.query_selector_all('img[src*="cover"], img[src*="hero"], img[src*="banner"]')
                for img in fallback_images:
                    src = await img.get_attribute('src')
                    if src and not src.startswith('data:') and src not in images:
                        images.append(src)

            # 去重并限制数量
            unique_images = list(dict.fromkeys(images))
            return unique_images[:10]  # 最多返回10张图片

        except Exception as e:
            logger.error(f"提取图片失败: {str(e)}")
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


    def _santize_html(self, html: str) -> str:
        """净化HTML，保留安全标签"""
        return bleach.clean(html or "", tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True)

    def _extract_images_from_html(self, html: str) -> List[str]:
         """从HTML中提取图片URL"""
         if not html:
            return []

         #用正则提取img标签的src属性
         img_pattern = r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>'
         matches = re.findall(img_pattern, html)

         #过滤掉data：开头的base64图片
         urls = [url for url in matches if not url.startswith('data:')]

         return list(dict.fromkeys(urls))


    def _rss_entry_html(self, entry) -> str:
        """获取RSS条目的HTML内容"""

        content = entry.get("content")
        if isinstance(content, list) and content:
            first = content[0]
            if isinstance(first, dict):
                val = first.get("value")
                if isinstance(val, str) and val:
                    return val

        summary_detail = entry.get("summary_detail")
        if isinstance(summary_detail, dict):
            val = summary_detail.get("value")
            if isinstance(val, str) and val:
                return val

        summary = entry.get("summary")
        if isinstance(summary, str) and summary:
            return summary

        return ""

    def _rss_entry_images(self, entry) -> List[str]:
        """提取RSS条目的图片"""
        urls = []

        #日志
        media_content = entry.get("media_content", []) or []

        for item in entry.get("media_content", []) or []:
            u = item.get("url")
            if u:
                urls.append(u)

        for item in entry.get("media_thumbnail", []) or []:
            u = item.get("url")
            if u:
                urls.append(u)

        for enc in entry.get("enclousures", []) or []:
            u = enc.get("href")
            if u:
                urls.append(u)

        html = self._rss_entry_html(entry)

        html_images = self._extract_images_from_html(html)

        urls += self._extract_images_from_html(html)

        return list(dict.fromkeys(urls))


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

                html = self._rss_entry_html(entry)
                sanitized = self._santize_html(html)

                images = self._rss_entry_images(entry)

                article_data = {
                        'title': entry.get('title', '无标题'),
                        'content': sanitized,
                        'url': link,
                        'author': entry.get('author', '未知作者'),
                        'published_at': self._parse_date(entry.get('published', '')), #type: ignore
                        'domain': urlparse(link).netloc if link else '', #type: ignore
                        'images': images,
                        'summary': ""#占位
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

