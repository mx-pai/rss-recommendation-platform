from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime

class SourceBase(BaseModel):
    name: str
    url: HttpUrl
    type: str = "rss"
    rss_url: Optional[HttpUrl] = None
    description: Optional[str] = None
    category: Optional[str] = None
    fetch_frequency: int = 60
    fetch_config: Optional[str] = None

class SourceCreate(SourceBase):
    pass

class SourceUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[HttpUrl] = None
    type: Optional[str] = None
    rss_url: Optional[HttpUrl] = None
    description: Optional[str] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None
    fetch_frequency: Optional[int] = None
    fetch_config: Optional[str] = None

class SourceResponse(SourceBase):
    id: int
    is_active: bool
    last_fetch: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class SourceListResponse(BaseModel):
    id: int
    name: str
    url: str
    type: str
    category: Optional[str] = None
    is_active: bool
    fetch_frequency: int
    fetch_config: Optional[str] = None
    last_fetch: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


    
