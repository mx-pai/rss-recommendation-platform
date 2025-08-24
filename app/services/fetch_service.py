import asyncio
from typing import Dict, List, Optional, cast, Any
from sqlalchemy.orm import Session
from app.models.content_source import ContentSource
from app.models.article import Article
from app.services.crawler import ModernWebCrawler, RSSCrawler
import logging
from datetime import datetime
import json
from bs4 import BeautifulSoup
import re


logger = logging.getLogger(__name__)

class FetchService:
    """抓取任务服务"""
    def __init__(self):
        self.web_crawler = ModernWebCrawler()
        self.rss_crawler = RSSCrawler()

    async def fetch_source(self, source_id: int, db: Session) -> Dict:
        """抓取指定内容源"""
        try:
            source = db.query(ContentSource).filter(ContentSource.id == source_id).first()
            if not source:
                return {"success": False, "error": "内容源不存在"}

            is_active = bool(getattr(source, "is_active"))
            if not is_active:
                return {"success": False, "error": "内容源已禁用"}

            source_type = cast(str, getattr(source, "type"))
            if source_type == "rss":
                return await self._fetch_rss_source(source, db)
            elif source_type == "manual":
                return await self._fetch_webpage_source(source, db)
            else:
                return {"success": False, "error": f"不支持的内容源类型: {source_type}"}
        except Exception as e:
            logger.error(f"抓取内容源失败{source_id}: {str(e)}")
            return {"success": False, "error": str(e)}


    async def _fetch_rss_source(self, source: ContentSource, db: Session) -> Dict:
        """抓取RSS源 - 获取全文内容"""
        try:
            rss_url_val = cast(Optional[str], getattr(source, "rss_url"))
            if not rss_url_val:
                return {"success": False, "error": "RSS URL 不存在"}

            rss_articles = self.rss_crawler.crawl_rss(rss_url_val)
            if not rss_articles:
                return {"success": False, "error": "RSS 抓取失败或无内容"}

            saved_count = 0
            total_found = len(rss_articles)

            for rss_article in rss_articles:
                article_url = rss_article.get('url', '')
                if not article_url:
                    logger.warning(f"跳过无URL的文章: {rss_article.get('title', '')}")
                    continue

                try:
                    full_article_data = await self.web_crawler.crawl_webpage(article_url)

                    if full_article_data and full_article_data.get('content'):
                        merged_article = {
                            'title': full_article_data.get('title') or rss_article.get('title', '无标题'),
                            'content': full_article_data.get('content', ''),  # 使用网页的完整内容
                            'url': article_url,
                            'author': full_article_data.get('author') or rss_article.get('author', '未知作者'),
                            'published_at': full_article_data.get('published_at') or rss_article.get('published_at'),
                            'images': full_article_data.get('images') or rss_article.get('images', []),
                            'summary': full_article_data.get('summary') ,
                            'domain': full_article_data.get('domain') or rss_article.get('domain', '')
                        }

                        if await self._save_article(merged_article, source, db):
                            saved_count += 1
                        else:
                            logger.info(f"文章已存在或保存失败: {merged_article['title']}")
                    else:
                        logger.warning(f"网页抓取失败，使用RSS数据: {article_url}")
                        if await self._save_article(rss_article, source, db):
                            saved_count += 1
                            logger.info(f"使用RSS数据保存文章: {rss_article['title']}")

                except Exception as e:
                    logger.error(f"处理文章失败 {article_url}: {str(e)}")
                    if await self._save_article(rss_article, source, db):
                        saved_count += 1
                        logger.info(f"使用RSS数据保存文章(异常回退): {rss_article['title']}")

            # 更新最后抓取时间
            source.last_fetch = datetime.now() # type: ignore[assignment]
            db.commit()

            return {
                "success": True,
                "message": f"成功抓取{saved_count} 篇文章(包含全文内容)",
                "total_found": total_found,
                "saved_count": saved_count
            }

        except Exception as e:
            logger.error(f"RSS 抓取失败: {str(e)}")
            return {"success": False, "error": str(e)}



    async def _fetch_webpage_source(self, source: ContentSource, db: Session) -> Dict:
        """抓取网页源"""
        try:
            source_url = cast(str, getattr(source, "url"))
            article_data = await self.web_crawler.crawl_webpage(source_url)

            if not article_data:
                return {"success": False, "error": "网页抓取失败"}

            processed = await self._save_article(article_data, source, db)

            #source.last_fetch = datetime.now()
            # db.commit()

            message = "成功保存新文章" if processed else "文章已存在，无需更新"
            if 'url' in article_data and processed:
                message = "成功更新文章"
            return {
                    "success": True,
                    "message": message,
                    "title": article_data.get('title', ''),
                    "url": article_data.get('url', '')
                    }

        except Exception as e:
            logger.error(f"网页抓取失败：{str(e)}")
            return {"success": False, "error": str(e)}

    async def _save_article(self, article_data: Dict, source: ContentSource, db: Session) -> bool:
        """保存文章到数据库(已存在则按需回填 images/summary/word_count/content)"""
        try:

            html = article_data.get('content', '') or ''
            text = BeautifulSoup(html, 'html.parser').get_text(separator='', strip=True)
            clean_text = re.sub(r'\s+', '', text)
            word_count_new = len(clean_text)
            images_list = article_data.get("images") or []

            existing_article = db.query(Article).filter(Article.url == article_data.get('url', '')).first()
            if existing_article:
                logger.info(f"文章已存在：{article_data.get('title', '')}")

                updated = False

                # 现有值
                word_count_val = cast(Optional[int], getattr(existing_article, 'word_count'))

                # 纯文本
                text = BeautifulSoup(html, 'html.parser').get_text(separator=' ', strip=True)

                # 与已存不同则更新
                if text and (word_count_val != len(text)):
                    setattr(existing_article, 'word_count', len(text))  # type: ignore[assignment]
                    updated = True

                if (not existing_article.images) and images_list:# type: ignore[assignment]
                    existing_article.images = json.dumps(images_list) # type: ignore[assignment]
                    updated = True
                if (existing_article.word_count or 0) == 0 and text: # type: ignore[assignment]
                    existing_article.word_count = len(text) # type: ignore[assignment]
                    updated = True

                new_summary = article_data.get('summary', '')
                if new_summary and new_summary != existing_article.summary:
                # 如果新摘要是AI生成的,就更新
                    if len(new_summary) > 50 and len(new_summary) < 500:
                        existing_article.summary = new_summary
                        updated = True
                        logger.info(f"更新AI摘要: {new_summary}")

                if  html: # type: ignore[assignment]
                    existing_article.content = html
                    updated = True

                if updated:
                    # 同时更新源的last_fetch
                    source.last_fetch = datetime.now() # type: ignore[assignment]
                    db.commit()
                    db.refresh(existing_article)
                    logger.info(f"已回填文章字段：{existing_article.title}")
                    return True
                else:
                    logger.info(f"文章已存在且无需更新:{existing_article.title}")
                return True


            db_article = Article(
                    title=article_data.get('title', "无标题"),
                    content=html,
                    url=article_data.get('url', ''),
                    author=article_data.get('author', '未知作者'),
                    published_at=article_data.get('published_at'),
                    source_id=source.id,
                    source_type=source.type,
                    is_read=False,
                    images=json.dumps(article_data.get('images', [])) if article_data.get('images') else None,
                    summary=article_data.get('summary', ''),
                    #word_count=len(text)
                    word_count=word_count_new
                    )

            db.add(db_article)

            # 同时更新源的last_fetch
            source.last_fetch = datetime.now() # type: ignore[assignment]

            db.commit()
            db.refresh(db_article)

            logger.info(f"成功保存文章: {db_article.title}")
            return True
        except Exception as e:
            logger.error(f"保存文章失败：{str(e)}")
            db.rollback()
            return False
    async def fetch_all_active_sources(self, db: Session) -> Dict:
        """抓取所有活动的内容源"""
        try:
            active_sources = db.query(ContentSource).filter(ContentSource.is_active == True).all()

            results: List[Dict[str, Any]] = []
            for source in active_sources:
                source_id_val = cast(int, getattr(source, "id"))
                fetch_result = await self.fetch_source(source_id_val, db)
                results.append({
                    "source_id": source_id_val,
                    "source_name": source.name,
                    "result": fetch_result
                    })
            return {
                    "success": True,
                    "message": f"完成{len(active_sources)}个内容源的抓取",
                    "result": results
                    }
        except Exception as e:
            logger.error(f"批量抓取失败：{str(e)}")
            return {"success": False, "error": str(e)}


