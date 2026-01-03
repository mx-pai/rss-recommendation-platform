import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.article import Article
from app.models.content_source import ContentSource
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.article import (
    ArticleCreate,
    ArticleListResponse,
    ArticleResponse,
    ArticleUpdate,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/articles", tags=["文章管理"])


@router.post("/", response_model=ArticleResponse)
def create_article(
    article_data: ArticleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建新文章"""
    source = (
        db.query(ContentSource)
        .filter(
            ContentSource.id == article_data.source_id,
            ContentSource.user_id == current_user.id,
        )
        .first()
    )
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="内容源不存在"
        )

    db_article = Article(
        title=article_data.title,
        content=article_data.content,
        url=str(article_data.url),
        author=article_data.author,
        published_at=article_data.published_at,
        source_id=article_data.source_id,
        source_type=article_data.source_type or source.type,
        user_id=current_user.id,
    )
    db.add(db_article)
    db.commit()
    db.refresh(db_article)

    return db_article


@router.get("/{article_id}", response_model=ArticleResponse)
def get_article(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取单个文章详情"""
    article = (
        db.query(Article)
        .filter(Article.id == article_id, Article.user_id == current_user.id)
        .first()
    )
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文章不存在")
    return article


@router.get("/", response_model=List[ArticleListResponse])
def get_articles(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(20, ge=1, le=100, description="返回的记录数"),
    source_id: Optional[int] = Query(None, description="按内容源筛选"),
    is_read: Optional[bool] = Query(None, description="按阅读状态筛选"),
    category: Optional[str] = Query(None, description="按分类筛选"),
    search: Optional[str] = Query(None, description="搜索标题或内容"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取文章列表，支持分页和筛选"""
    try:
        query = (
            db.query(Article)
            .join(ContentSource, Article.source_id == ContentSource.id)
            .filter(Article.user_id == current_user.id)
        )

        # 应用筛选条件
        if source_id is not None:
            query = query.filter(Article.source_id == source_id)

        if is_read is not None:
            query = query.filter(Article.is_read == is_read)

        if category:
            query = query.filter(ContentSource.category == category)

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (Article.title.ilike(search_term))
                | (Article.content.ilike(search_term))
                | (Article.summary.ilike(search_term))
            )

        # 按创建时间倒序排列
        query = query.order_by(Article.created_at.desc())

        # 应用分页
        total = query.count()
        articles = query.offset(skip).limit(limit).all()

        logger.info(
            f"查询文章列表: 总数={total}, 返回={len(articles)}, 筛选条件: source_id={source_id}, is_read={is_read}, category={category}, search={search}"
        )

        return articles

    except Exception as e:
        logger.error(f"查询文章列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="查询文章列表失败")


@router.put("/{article_id}", response_model=ArticleResponse)
def update_article(
    article_id: int,
    article_data: ArticleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新文章"""
    article = (
        db.query(Article)
        .filter(Article.id == article_id, Article.user_id == current_user.id)
        .first()
    )
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文章不存在")
    update_data = article_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(article, field, value)

    db.commit()
    db.refresh(article)

    return article


@router.delete("/{article_id}")
def delete_article(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除文章"""
    article = (
        db.query(Article)
        .filter(Article.id == article_id, Article.user_id == current_user.id)
        .first()
    )
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文章不存在")
    db.delete(article)
    db.commit()
    return {"message": "文章删除成功"}


@router.patch("/{article_id}/toggle-read")
def toggle_article_read_status(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """切换文章阅读状态"""
    article = (
        db.query(Article)
        .filter(Article.id == article_id, Article.user_id == current_user.id)
        .first()
    )
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文章不存在")

    article.is_read = not article.is_read
    db.commit()
    db.refresh(article)

    status_text = "已读" if article.is_read else "未读"

    return {"message": f"文章已标记为{status_text}"}
