from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine
from app.models import user, content_source, article
from app.routers import auth
from app.routers import sources
from app.routers import articles
from app.routers import admin
from app.services.scheduler import scheduler_service
import logging

logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] %(name)s - %(message)s"
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
app.include_router(admin.router)

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
            "scheduler": scheduler_service.get_status()["running"],
            "models": ["User", "ContentSource", "Article"]
            }


@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("应用启动中...")
    logger.info("数据库: PostgreSQL")
    logger.info("缓存: Redis")
    logger.info("=" * 60)

    # 启动定时任务调度器
    try:
        scheduler_service.start()
        logger.info("定时任务调度器启动成功")
    except Exception as e:
        logger.error(f"定时任务调度器启动失败: {str(e)}")

    logger.info("=" * 60)
    logger.info("应用启动完成！")
    logger.info("API文档: http://localhost:8000/docs")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行"""
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("应用关闭中...")

    # 停止定时任务调度器
    try:
        scheduler_service.stop()
        logger.info("定时任务调度器已停止")
    except Exception as e:
        logger.error(f"停止调度器失败: {str(e)}")

    logger.info("再见！")
    logger.info("=" * 60)


