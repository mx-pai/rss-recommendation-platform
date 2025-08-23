from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class ContentSource(Base):
    __tablename__ = "content_sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, comment="源名称")
    url = Column(String(500), unique=True, nullable=False, comment="源URL")
    type = Column(String(50), nullable=False, comment="源类型：rss, manual, api")
    rss_url = Column(String(500), comment="RSS URL (如果是RSS源)")
    description = Column(Text, comment="源描述")
    category = Column(String(100), comment="分类")
    is_active = Column(Boolean, default=True)
    fetch_frequency = Column(Integer, default=60, comment="抓取频率（分钟）")
    fetch_config = Column(Text, comment="抓取配置JSON")
    last_fetch = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
 
    articles = relationship("Article", back_populates="source", cascade="all, delete-orphan", passive_deletes=True)
    

