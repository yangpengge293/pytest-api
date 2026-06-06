"""
SQLAlchemy ORM 模型 - MySQL 持久化
"""
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, Enum, JSON, Boolean,
)
from sqlalchemy.orm import relationship

from backend.database import Base


class TestCase(Base):
    """测试用例表 - 与 Excel 列一一对应，非技术人员在 UI 维护"""
    __tablename__ = "test_cases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, comment="用例名称")
    method = Column(String(10), nullable=False, default="GET", comment="请求方法")
    path = Column(String(500), nullable=False, comment="请求路径")
    headers = Column(Text, comment="请求头(JSON)")
    body = Column(Text, comment="请求参数(JSON)")
    expected_status = Column(Integer, default=200, comment="预期状态码")
    expected_fields = Column(Text, comment="预期响应字段(JSON)")

    # 分类与排序
    module = Column(String(100), default="", comment="所属模块（对应Excel的Sheet/文件）")
    priority = Column(Enum("P0", "P1", "P2", "P3"), default="P1", comment="优先级")
    is_active = Column(Boolean, default=True, comment="是否启用")
    sort_order = Column(Integer, default=0, comment="执行顺序")

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关联
    suite_links = relationship("SuiteCase", back_populates="case", cascade="all, delete-orphan")


class TestSuite(Base):
    """测试套件表 - 将多个用例组合成一组执行"""
    __tablename__ = "test_suites"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, comment="套件名称")
    description = Column(Text, comment="描述")
    env = Column(String(50), comment="指定环境（为空则用config.yaml的active_env）")

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关联
    suite_links = relationship("SuiteCase", back_populates="suite", cascade="all, delete-orphan")
    executions = relationship("Execution", back_populates="suite")


class SuiteCase(Base):
    """套件-用例 多对多关联表"""
    __tablename__ = "suite_cases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    suite_id = Column(Integer, ForeignKey("test_suites.id", ondelete="CASCADE"))
    case_id = Column(Integer, ForeignKey("test_cases.id", ondelete="CASCADE"))
    sort_order = Column(Integer, default=0, comment="套件内排序顺序")

    suite = relationship("TestSuite", back_populates="suite_links")
    case = relationship("TestCase", back_populates="suite_links")


class Execution(Base):
    """执行记录表"""
    __tablename__ = "executions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    suite_id = Column(Integer, ForeignKey("test_suites.id"), nullable=True, comment="关联套件（为空=全量执行）")
    env = Column(String(50), nullable=False, comment="执行环境")

    status = Column(
        Enum("pending", "running", "passed", "failed", "error"),
        default="pending", comment="执行状态",
    )
    trigger_type = Column(
        Enum("manual", "scheduled", "ci"), default="manual", comment="触发方式",
    )
    total = Column(Integer, default=0, comment="总用例数")
    passed = Column(Integer, default=0, comment="通过数")
    failed = Column(Integer, default=0, comment="失败数")
    error = Column(Integer, default=0, comment="异常数")

    duration = Column(String(50), comment="执行耗时")
    report_path = Column(String(500), comment="Allure报告路径")
    celery_task_id = Column(String(255), comment="Celery任务ID")

    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    # 关联
    suite = relationship("TestSuite", back_populates="executions")
    results = relationship("TestResult", back_populates="execution", cascade="all, delete-orphan")


class TestResult(Base):
    """单条用例执行结果"""
    __tablename__ = "test_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    execution_id = Column(Integer, ForeignKey("executions.id", ondelete="CASCADE"))

    case_id = Column(Integer, comment="关联用例ID")
    case_name = Column(String(200), comment="用例名称快照")
    method = Column(String(10), comment="请求方法快照")
    path = Column(String(500), comment="请求路径快照")

    status = Column(Enum("passed", "failed", "error", "skipped"), comment="结果状态")
    actual_status_code = Column(Integer, comment="实际状态码")
    actual_response = Column(Text, comment="实际响应体(截断)")
    error_message = Column(Text, comment="错误信息")

    duration_ms = Column(Integer, comment="单条耗时(ms)")
    created_at = Column(DateTime, default=datetime.now)

    execution = relationship("Execution", back_populates="results")
