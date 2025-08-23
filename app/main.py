from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine
from app.models import user, content_source, article
from app.routers import auth
from app.routers import sources
from app.routers import articles
import logging

logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s%(name)s:%(message)s"
        )

# 数据库表创建
user.Base.metadata.create_all(bind=engine)
content_source.Base.metadata.create_all(bind=engine)
article.Base.metadata.create_all(bind=engine)

app = FastAPI(
        title=settings.app_name,
        debug=settings.debug
        )

app.add_middleware(
        CORSMiddleware,
        allow_origins = ["*"],
        allow_credentials = True,
        allow_methods = ["*"],
        allow_headers = ["*"],
        )

app.include_router(auth.router)
app.include_router(sources.router)
app.include_router(articles.router)

@app.get("/")
async def root():
    return {"message": "智能内容聚合平台API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "database": "connected"}

@app.get("/api/v1/status")
async def api_status():
    return {
            "api_version": "v1",
            "status": "running",
            "database": "PostgreSQL",
            "cache": "Redis",
            "models": ["User", "ContentSource", "Atticle"]
            }


