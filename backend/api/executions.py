"""
执行管理接口 - 手动执行 / 定时执行 / CI触发
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Execution, TestResult, TestSuite
from backend.schemas import ExecutionCreate, ExecutionOut, ResultOut, ApiResponse, PageResponse
from backend.services.celery_tasks import trigger_execution

router = APIRouter(prefix="/executions", tags=["执行管理"])


@router.get("", response_model=PageResponse)
def list_executions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    db: Session = Depends(get_db),
):
    """分页查询执行记录"""
    query = db.query(Execution)
    if status:
        query = query.filter(Execution.status == status)
    total = query.count()
    records = query.order_by(Execution.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return PageResponse(
        data=[ExecutionOut.model_validate(r).model_dump() for r in records],
        total=total, page=page, page_size=page_size,
    )


@router.get("/{exec_id}", response_model=ApiResponse)
def get_execution(exec_id: int, db: Session = Depends(get_db)):
    """获取执行详情"""
    record = db.query(Execution).get(exec_id)
    if not record:
        return ApiResponse(code=404, message="执行记录不存在")
    return ApiResponse(data=ExecutionOut.model_validate(record).model_dump())


@router.get("/{exec_id}/results", response_model=ApiResponse)
def get_execution_results(exec_id: int, db: Session = Depends(get_db)):
    """获取某次执行的所有用例结果"""
    results = db.query(TestResult).filter(TestResult.execution_id == exec_id).all()
    return ApiResponse(data=[ResultOut.model_validate(r).model_dump() for r in results])


@router.post("/run", response_model=ApiResponse)
def run_tests(data: ExecutionCreate, db: Session = Depends(get_db)):
    """
    触发测试执行（异步）

    - suite_id 为空：执行所有启用用例
    - suite_id 有值：只执行该套件关联的用例
    - trigger_type: manual（手动）/ scheduled（定时）/ ci（CI触发）
    """
    # 解析环境：优先指定env > 套件env > config.yaml active_env
    import yaml, os
    env = data.env
    if not env and data.suite_id:
        suite = db.query(TestSuite).get(data.suite_id)
        if suite and suite.env:
            env = suite.env
    if not env:
        # 从项目根目录读取 config.yaml
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        config_path = os.path.join(project_root, "config", "config.yaml")
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        env = cfg.get("active_env", "test2")

    # 创建执行记录
    record = Execution(
        suite_id=data.suite_id, env=env,
        status="pending", trigger_type=data.trigger_type,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    # 异步触发 Celery 任务
    task = trigger_execution.delay(record.id, data.suite_id, env)
    record.celery_task_id = task.id
    db.commit()

    return ApiResponse(
        message=f"执行任务已提交，任务ID: {task.id}",
        data=ExecutionOut.model_validate(record).model_dump(),
    )


@router.post("/ci/trigger", response_model=ApiResponse)
def ci_trigger(suite_id: int | None = None, env: str | None = None):
    """CI 触发接口（供 Jenkins/GitLab CI 等调用）"""
    data = ExecutionCreate(suite_id=suite_id, env=env, trigger_type="ci")
    from backend.database import SessionLocal
    db = SessionLocal()
    try:
        return run_tests(data, db)
    finally:
        db.close()
