"""
管理员路由 - 用于管理定时任务和系统配置
"""
from fastapi import APIRouter, Depends, HTTPException
from app.routers.auth import get_current_user
from app.models.user import User
from app.services.scheduler import scheduler_service
import logging

router = APIRouter(prefix="/admin", tags=["管理"])
logger = logging.getLogger(__name__)


@router.post("/scheduler/start")
async def start_scheduler(current_user: User = Depends(get_current_user)):
    """
    启动定时任务调度器

    需要认证后才能操作
    """
    try:
        scheduler_service.start()
        return {
            "success": True,
            "message": "定时任务调度器已启动",
            "status": scheduler_service.get_status()
        }
    except Exception as e:
        logger.error(f"启动调度器失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"启动失败: {str(e)}")


@router.post("/scheduler/stop")
async def stop_scheduler(current_user: User = Depends(get_current_user)):
    """
    停止定时任务调度器

    需要认证后才能操作
    """
    try:
        scheduler_service.stop()
        return {
            "success": True,
            "message": "定时任务调度器已停止"
        }
    except Exception as e:
        logger.error(f"停止调度器失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"停止失败: {str(e)}")


@router.get("/scheduler/status")
async def get_scheduler_status(current_user: User = Depends(get_current_user)):
    """
    查看调度器状态

    返回调度器是否运行、任务列表、下次运行时间等信息
    """
    status = scheduler_service.get_status()
    return {
        "success": True,
        "data": status
    }


@router.post("/scheduler/jobs/{job_id}/pause")
async def pause_job(job_id: str, current_user: User = Depends(get_current_user)):
    """
    暂停指定任务

    Args:
        job_id: 任务ID
    """
    try:
        scheduler_service.pause_job(job_id)
        return {
            "success": True,
            "message": f"任务 {job_id} 已暂停"
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"任务不存在或暂停失败: {str(e)}")


@router.post("/scheduler/jobs/{job_id}/resume")
async def resume_job(job_id: str, current_user: User = Depends(get_current_user)):
    """
    恢复指定任务

    Args:
        job_id: 任务ID
    """
    try:
        scheduler_service.resume_job(job_id)
        return {
            "success": True,
            "message": f"任务 {job_id} 已恢复"
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"任务不存在或恢复失败: {str(e)}")


@router.post("/scheduler/trigger-now")
async def trigger_fetch_now(current_user: User = Depends(get_current_user)):
    """
    立即触发一次抓取任务（不等待定时）

    适用于需要立即更新内容的场景
    """
    try:
        import asyncio
        # 在后台运行，不阻塞响应
        asyncio.create_task(scheduler_service.fetch_all_active_sources())

        return {
            "success": True,
            "message": "抓取任务已触发，正在后台执行"
        }
    except Exception as e:
        logger.error(f"触发抓取失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"触发失败: {str(e)}")


# TODO: 添加更多管理功能
# - 查看系统统计信息
# - 管理用户权限
# - 查看日志
# - 系统配置管理
