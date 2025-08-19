from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from datetime import datetime

class ArticleBase(BaseModel):
    title: str
    content: Optional[str] = None
    url: HttpUrl
    author: Optional[str] = None
    published_at: Optional[datetime] = None
    source_type: Optional[str] = None
    images: Optional[List[str]] = None
    summary: Optional[str] = None
    word_count: int = 0

class ArticleCreate(ArticleBase):
    source_id: int

class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    author: Optional[str] = None
    published_at: Optional[datetime] = None
    source_type: Optional[str] = None
    is_read: Optional[bool] = None
    images: Optional[List[str]] = None
    summary: Optional[str] = None
    word_count: int = 0

class ArticleResponse(ArticleBase):
    id: int
    source_id: int
    is_read: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    class Config:
        from_attributes = True

class ArticleListResponse(BaseModel):
    id: int
    title: str
    url: str
    author: Optional[str] = None
    source_type: Optional[str] = None
    is_read: bool
    published_at: Optional[datetime] = None
    created_at: datetime
    images: Optional[List[str]] = None
    summary: Optional[str] = None
    word_count: int = 0

    class Config:
        from_attributes = True

