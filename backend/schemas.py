"""
Pydantic 请求/响应模型
"""
from datetime import datetime
from pydantic import BaseModel, Field


# ========== TestCase ==========
class CaseCreate(BaseModel):
    name: str = Field(..., description="用例名称")
    method: str = Field("GET", description="请求方法")
    path: str = Field(..., description="请求路径")
    headers: str | None = Field(None, description="请求头(JSON)")
    body: str | None = Field(None, description="请求参数(JSON)")
    expected_status: int = Field(200, description="预期状态码")
    expected_fields: str | None = Field(None, description="预期响应字段(JSON)")
    module: str = Field("", description="所属模块")
    priority: str = Field("P1", description="优先级")
    is_active: bool = Field(True, description="是否启用")
    sort_order: int = Field(0, description="执行顺序")


class CaseUpdate(BaseModel):
    name: str | None = None
    method: str | None = None
    path: str | None = None
    headers: str | None = None
    body: str | None = None
    expected_status: int | None = None
    expected_fields: str | None = None
    module: str | None = None
    priority: str | None = None
    is_active: bool | None = None
    sort_order: int | None = None


class CaseOut(CaseCreate):
    id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


# ========== TestSuite ==========
class SuiteCreate(BaseModel):
    name: str = Field(..., description="套件名称")
    description: str | None = Field(None, description="描述")
    env: str | None = Field(None, description="指定环境")
    case_ids: list[int] = Field(default_factory=list, description="关联用例ID列表")


class SuiteUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    env: str | None = None
    case_ids: list[int] | None = None


class SuiteOut(BaseModel):
    id: int
    name: str
    description: str | None
    env: str | None
    case_ids: list[int] = Field(default_factory=list)
    case_count: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


# ========== Execution ==========
class ExecutionCreate(BaseModel):
    suite_id: int | None = Field(None, description="套件ID（为空则执行所有启用的用例）")
    env: str | None = Field(None, description="指定环境（为空则用config.yaml的active_env）")
    trigger_type: str = Field("manual", description="触发方式: manual/scheduled/ci")


class ExecutionOut(BaseModel):
    id: int
    suite_id: int | None
    env: str
    status: str
    trigger_type: str
    total: int
    passed: int
    failed: int
    error: int
    duration: str | None
    report_path: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime | None

    model_config = {"from_attributes": True}


# ========== TestResult ==========
class ResultOut(BaseModel):
    id: int
    case_id: int | None
    case_name: str | None
    method: str | None
    path: str | None
    status: str | None
    actual_status_code: int | None
    actual_response: str | None
    error_message: str | None
    duration_ms: int | None
    created_at: datetime | None

    model_config = {"from_attributes": True}


# ========== 通用响应 ==========
class ApiResponse(BaseModel):
    code: int = 0
    message: str = "success"
    data: dict | list | None = None


class PageResponse(BaseModel):
    code: int = 0
    message: str = "success"
    data: list = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20
