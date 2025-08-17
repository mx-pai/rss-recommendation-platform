from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

#数据库引擎
engine = create_engine(settings.database_url)

#会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

#基础模型类
Base = declarative_base()

#获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
