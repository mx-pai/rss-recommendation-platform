import asyncio
from typing import Dict, List, Optional, cast, Any
from sqlalchemy.orm import Session
from app.models.content_source import ContentSource
from app.models.article import Article
from app.services.crawler import ModernWebCrawler, RSSCrawler
import logging
from datetime import datetime
import json


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
        """抓取RSS源"""
        try:
            rss_url_val = cast(Optional[str], getattr(source, "rss_url"))
            if not rss_url_val:
                return {"success": False, "error": "RSS URL 不存在"}

            articles = self.rss_crawler.crawl_rss(rss_url_val)

            if not articles:
                return {"success": False, "error": "RSS 抓取失败或无内容"}

            saved_count = 0
            for article_data in articles:
                if await self._save_article(article_data, source, db):
                    saved_count += 1

            source.last_fetch = datetime.now() # type: ignore[assignment]
            db.commit()

            return {
                    "success": True,
                    "message": f"成功抓取{saved_count} 篇文章",
                    "total_found": len(articles),
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

            if await self._save_article(article_data, source, db):

                source.last_fetch = datetime.now() # type: ignore[assignment]
                db.commit()

                return {
                        "success": True,
                        "message": "成功抓取网页内容",
                        "title": article_data.get('title', ''),
                        "url": article_data.get('url', '')
                        }
            else:
                return {"success": False, "error": "保存文章失败"}

        except Exception as e:
            logger.error(f"网页抓取失败：{str(e)}")
            return {"success": False, "error": str(e)}

    async def _save_article(self, article_data: Dict, source: ContentSource, db: Session) -> bool:
        """保存文章到数据库"""
        try:
            existing_article = db.query(Article).filter(Article.url == article_data.get('url', '')).first()
            if existing_article:
                logger.info(f"文章已存在：{article_data.get('title', '')}")
                return False

            db_article = Article(
                    title=article_data.get('title', "无标题"),
                    content=article_data.get('content', ''),
                    url=article_data.get('url', ''),
                    author=article_data.get('author', '未知作者'),
                    published_at=article_data.get('published_at'),
                    source_id=source.id,
                    source_type=source.type,
                    is_read=False,
                    images=json.dumps(article_data.get('images', [])) if article_data.get('images') else None,
                    summary=article_data.get('summary', ''),
                    word_count=len(article_data.get('content', '')) if article_data.get('content') else 0
                    )
            db.add(db_article)
            db.commit()
            db.refresh(db_article)

            logger.info(f"成功保存文章: {db_article.title}")
            return True
        except Exception as e:
            logger.error(f"保存文章失败：{str(e)}")
            db.rollback()
            return False
    async def fetch_all_actice_sources(self, db: Session) -> Dict:
        """抓取所有活动的内容源"""
        try:
            actice_sources = db.query(ContentSource).filter(ContentSource.is_active == True).all()

            results: List[Dict[str, Any]] = []
            for source in actice_sources:
                source_id_val = cast(int, getattr(source, "id"))
                fetch_result = await self.fetch_source(source_id_val, db)
                results.append({
                    "source_id": source_id_val,
                    "source_name": source.name,
                    "result": fetch_result
                    })
            return {
                    "success": True,
                    "message": f"完成{len(actice_sources)}个那内容源的抓取",
                    "result": results
                    }
        except Exception as e:
            logger.error(f"批量抓取失败：{str(e)}")
            return {"success": False, "error": str(e)}


