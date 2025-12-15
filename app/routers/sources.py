from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.schemas.source import SourceCreate, SourceUpdate, SourceResponse, SourceListResponse
from app.models.content_source import ContentSource
from app.routers.auth import get_current_user
from app.models.user import User
from app.services.fetch_service import FetchService


router = APIRouter(prefix="/sources", tags=["内容源管理"])

@router.post("/", response_model=SourceResponse)
def content_source(
        source_data: SourceCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
        ):
    """创建新的内容源"""
    if db.query(ContentSource).filter(ContentSource.url == str(source_data.url)).first():
        raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="URL已存在"
                )

    db_source = ContentSource(
            name=source_data.name,
            url=str(source_data.url),
            type=source_data.type,
            rss_url=str(source_data.rss_url) if source_data.rss_url else None,
            description=source_data.description,
            category=source_data.category,
            is_active=True,
            fetch_frequency=source_data.fetch_frequency,
            fetch_config=source_data.fetch_config,
            user_id=current_user.id
            )
    db.add(db_source)
    db.commit()
    db.refresh(db_source)

    return db_source

@router.get("/", response_model=List[SourceListResponse])
def get_sources(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
        ):
    """获取内容源列表"""
    sources = db.query(ContentSource).offset(skip).limit(limit).all()
    return sources

@router.get("/{source_id}", response_model=SourceResponse)
def get_source(
        source_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
        ):
    """获取单个内容源详情"""
    source = db.query(ContentSource).filter(ContentSource.id == source_id).first()
    if not source:
        raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="内容源不存在"
                )
    return source

@router.put("/{source_id}", response_model=SourceResponse)
def update_source(
        source_id: int,
        source_data: SourceUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
        ):
    """更新内容源"""
    source = db.query(ContentSource).filter(ContentSource.id == source_id).first()
    if not source:
        raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="内容源不存在"
                )
    update_data = source_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field == "url" and value:
            value = str(value)
        elif field == "rss_url" and value:
            value = str(value)
        setattr(source, field, value)
    db.commit()
    db.refresh(source)

    return source

@router.delete("/{source_id}")
def delete_source(
        source_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
        ):
    """删除内容源"""
    source = db.query(ContentSource).filter(ContentSource.id == source_id).first()
    if not source:
        raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="内容源不存在"
                )
    db.delete(source)
    db.commit()

    return {"message": "内容源删除成功"}

@router.patch("/{source_id}/toggle")
def toggle_source_status(
        source_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
        ):
    """切换内容源状态（启用/禁用）"""
    source = db.query(ContentSource).filter(ContentSource.id == source_id).first()
    if not source:
        raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="内容源不存在"
                )
    source.is_active = not bool(source.is_active) # type: ignore
    db.commit()
    db.refresh(source)
    return {"message": f"内容源已{'启用' if source.is_active else '禁用'}"} #type: ignore


@router.post("/{source_id}/fetch")
async def fetch_service_content(
        source_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
        ):
    """手动抓取指定内容"""
    # 验证用户是否拥有该内容源
    source = db.query(ContentSource).filter(
            ContentSource.id == source_id,
            ContentSource.user_id == current_user.id
    ).first()
    if not source:
        raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="内容源不存在"
                )

    fetch_service = FetchService()
    result = await fetch_service.fetch_source(source_id, db)
    return result

@router.post("/fetch-all")
async def fetch_all_source(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
        ):
    """抓取所有启用的内容源"""
    fetch_service = FetchService()
    result = await fetch_service.fetch_all_active_sources(db, current_user.id)
    return result



