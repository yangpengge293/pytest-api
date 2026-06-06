"""
Celery 异步任务 + 定时调度（Beat）

开发模式（DB_TYPE=sqlite）：使用 eager 模式，任务同步执行，无需 Redis
生产模式（DB_TYPE=mysql）：使用 Redis 作为 broker，支持异步和定时调度
"""
from celery import Celery
from celery.schedules import crontab

from backend.config import settings

# 创建 Celery 实例
if settings.IS_SQLITE:
    # 开发模式：eager 模式（同步执行，无需 Redis）
    celery_app = Celery("pytest_api")
    celery_app.conf.update(
        task_always_eager=True,
        task_eager_propagates=True,
    )
else:
    # 生产模式：使用 Redis
    celery_app = Celery(
        "pytest_api",
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND,
    )
    celery_app.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="Asia/Shanghai",
        enable_utc=True,
        task_track_started=True,
        beat_schedule={
            "daily-regression": {
                "task": "backend.services.celery_tasks.trigger_execution",
                "schedule": crontab(hour=2, minute=0),
                "args": (None, None, "test2"),
                "kwargs": {"trigger_type": "scheduled"},
            },
        },
    )


@celery_app.task(bind=True, name="backend.services.celery_tasks.trigger_execution")
def trigger_execution(self, execution_id: int, suite_id: int | None, env: str, trigger_type: str = "manual"):
    """
    异步执行测试套件

    参数:
        execution_id: 执行记录ID
        suite_id: 套件ID（None=全量执行）
        env: 环境名称
        trigger_type: 触发方式
    """
    from backend.services.runner import run_suite
    from backend.database import SessionLocal
    from backend.models import Execution

    # 更新触发方式
    if trigger_type != "manual":
        db = SessionLocal()
        try:
            record = db.query(Execution).get(execution_id)
            if record:
                record.trigger_type = trigger_type
                db.commit()
        finally:
            db.close()

    run_suite(execution_id, suite_id, env)
    return {"execution_id": execution_id, "status": "completed"}
