from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, comment="文章内容")
    url = Column(String(500), unique=True, nullable=False)
    author = Column(String(100), comment="作者")
    published_at = Column(DateTime(timezone=True))
    source_id = Column(Integer, ForeignKey("content_sources.id", onupdate="CASCADE"), nullable=False, comment="来源ID")
    source_type = Column(String(50), comment="来源类型：rss, manual, api")
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())   
    images = Column(Text, comment="图片URL列表（JSON格式）")
    summary = Column(Text, comment="文章摘要")
    word_count = Column(Integer, default=0, comment="字数统计")

    source = relationship("ContentSource", back_populates="articles")




                       
