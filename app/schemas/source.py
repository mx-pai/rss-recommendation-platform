from pydantic import BaseModel, HttpUrl, Field, ConfigDict, model_validator
from typing import Optional
from datetime import datetime
from enum import Enum
from typing_extensions import Annotated


PositiveInt = Annotated[int, Field(gt=0)]

class SourceType(str, Enum):
    rss = "rss"
    manual = "manual"
    api = "api"

class SourceBase(BaseModel):
    name: str
    url: HttpUrl
    type: SourceType = SourceType.rss
    rss_url: Optional[HttpUrl] = None
    description: Optional[str] = None
    category: Optional[str] = None
    fetch_frequency: PositiveInt = 60
    fetch_config: Optional[str] = None

class SourceCreate(SourceBase):
    @model_validator(mode="after")
    def validate_rss_url_for_rss(self):
        if self.type == SourceType.rss and not self.rss_url:
            raise ValueError("当 type='rss' 时必须提供 rss_url")
        return self


class SourceUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[HttpUrl] = None
    type: Optional[str] = None
    rss_url: Optional[HttpUrl] = None
    description: Optional[str] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None
    fetch_frequency: Optional[PositiveInt] = None
    fetch_config: Optional[str] = None

class SourceResponse(SourceBase):
    id: int
    is_active: bool
    last_fetch: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
    #class Config:
        #from_attributes = True

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
    model_config = ConfigDict(from_attributes=True)

    #class Config:
        #from_attributes = True


    
