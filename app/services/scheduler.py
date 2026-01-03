from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.core.database import SessionLocal
from app.models.content_source import ContentSource
from app.services.fetch_service import FetchService
import logging
import asyncio

logger = logging.getLogger(__name__)


class SchedulerService:
    """定时任务调度服务"""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.fetch_service = FetchService()
        self._is_running = False

    async def fetch_all_active_sources(self):
        """
        定时任务: 抓取所有活跃的内容源
        """
        logger.info("=" * 60)
        logger.info("开始执行定时抓取任务...")

        db = SessionLocal()
        try:
            # 查询所有启用的内容源
            sources = db.query(ContentSource).filter(
                ContentSource.is_active == True
            ).all()

            if not sources:
                logger.info("没有活跃的内容源需要抓取")
                return

            logger.info(f"发现 {len(sources)} 个活跃源，开始抓取...")

            success_count = 0
            error_count = 0

            # 逐个抓取
            for source in sources:
                try:
                    logger.info(f"正在抓取: {source.name} ({source.url})")

                    # 调用抓取服务
                    result = await self.fetch_service.fetch_from_source(
                        source_id=source.id,
                        db=db,
                        use_ai=False  # 默认不使用AI，避免费用过高
                    )

                    if result:
                        success_count += 1
                        logger.info(f"抓取成功: {source.name}")
                    else:
                        error_count += 1
                        logger.warning(f"抓取失败: {source.name}")

                except Exception as e:
                    error_count += 1
                    logger.error(f"抓取异常 {source.name}: {str(e)}")

                # 避免请求过快，稍微延迟
                await asyncio.sleep(2)

            logger.info(f"定时抓取任务完成！成功: {success_count}, 失败: {error_count}")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"定时任务执行失败: {str(e)}")

        finally:
            db.close()

    def start(self):
        """启动调度器"""
        if self._is_running:
            logger.warning("调度器已在运行中")
            return

        try:
            # 添加定时任务 - 每小时执行一次
            self.scheduler.add_job(
                self.fetch_all_active_sources,
                trigger=IntervalTrigger(hours=1),  # 每小时执行
                id="fetch_rss_sources",
                name="抓取RSS源",
                replace_existing=True,
                max_instances=1,  # 同时只运行一个实例
                misfire_grace_time=300  # 错过执行时间5分钟内仍然执行
            )
            self.scheduler.start()
            self._is_running = True
            logger.info("定时任务调度器已启动")
            logger.info("抓取频率: 每小时一次")

        except Exception as e:
            logger.error(f"启动调度器失败: {str(e)}")
            raise

    def stop(self):
        """停止调度器"""
        if not self._is_running:
            logger.warning("调度器未运行")
            return

        try:
            self.scheduler.shutdown(wait=True)
            self._is_running = False
            logger.info("定时任务调度器已停止")

        except Exception as e:
            logger.error(f"停止调度器失败: {str(e)}")
            raise

    def get_status(self):
        """获取调度器状态"""
        jobs = []
        if self._is_running:
            for job in self.scheduler.get_jobs():
                jobs.append({
                    "id": job.id,
                    "name": job.name,
                    "next_run": str(job.next_run_time) if job.next_run_time else None,
                    "trigger": str(job.trigger)
                })

        return {
            "running": self._is_running,
            "jobs": jobs,
            "job_count": len(jobs)
        }

    def pause_job(self, job_id: str):
        """暂停指定任务"""
        try:
            self.scheduler.pause_job(job_id)
            logger.info(f"任务 {job_id} 已暂停")
        except Exception as e:
            logger.error(f"暂停任务失败: {str(e)}")
            raise

    def resume_job(self, job_id: str):
        """恢复指定任务"""
        try:
            self.scheduler.resume_job(job_id)
            logger.info(f"任务 {job_id} 已恢复")
        except Exception as e:
            logger.error(f"恢复任务失败: {str(e)}")
            raise


scheduler_service = SchedulerService()
