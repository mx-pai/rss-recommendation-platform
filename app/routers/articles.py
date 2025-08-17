from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.schemas.article import AeticleUpdate, ArticleResponse, ArticleCreate, ArticleListResponse
from app.models.article import Article
from app.models.content_source import ContentSource
from app.routers.auth import get_current_user
from app.models.user import User
from app.core.crud_utils import get_object_or_404
router = APIRouter(prefix="/articles", tags=["文章管理"])


@router.post("/", response_model=ArticleResponse)
def create_article(
        article_data: ArticleCreate,
        db, Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
        ):
    """创建新文章"""
    source = get_object_or_404(db, ContentSource, article_data.source_id, "内容源不存在")
    db_article = Article(
            title=article_data.title,
            content=article_data.content,
            url=str(article_data.url),
            author=article_data.author,
            published_at=article_data.published_at,
            source_id=article_data.source_id,
            source_type=article_data.source_type or source.type
            )
    db.add(db.article)
    db.commit()
    db.refresh(db.article)

    return db.article

@router.get("/{article_id}", response_model=ArticleResponse)
def get_article(
        article_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
        ):
    """获取单个文章详情"""
    article = get_object_or_404(db, Article, article_id, "文章不存在")
    return article

@router.put("/{article_id}", response_model=ArticleResponse)
def update_article(
        article_id: int,
        article_data: AeticleUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
        ):
    """更新文章"""
    article = get_object_or_404(db, Article, article_id, "文章不存在")
    update_data = article_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(article, field, value)

    db.commit()
    db.refresh(article)
    
    return article

@router.delete("/{article_id}")
def delete_article(
        articel_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
        ):
    """删除文章"""
    article = get_object_or_404(db, Article, articel_id, "文章不存在")
    db.delete(article)
    db.commit()
    return {"message": "文章删除成功"}

@router.patch("/{article_id}/toggle-read")
def toggle_article_read_status(
        article_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
        ):
    """切换文章阅读状态"""
    article = get_object_or_404(db, Article, article_id, "文章不存在")

    article.is_read = not article.isread
    db.commit()
    db.refresh(article)

    status_text = "已读" if article.is_read else "未读"

    return {"message": f"文章已标记为{status_text}"}

