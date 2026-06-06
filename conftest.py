import os
import pytest
import yaml
from utils.http_client import HttpClient
from utils.excel_reader import ExcelReader
from utils.logger import logger

# 项目根目录
BASE_DIR = os.path.dirname(__file__)


def pytest_addoption(parser):
    """注册命令行参数"""
    parser.addoption(
        "--env",
        action="store",
        default=None,
        help="指定运行环境（覆盖 config.yaml 中的 active_env），可选值：test2 / ready2 / prod",
    )
    parser.addoption(
        "--source",
        action="store",
        default=None,
        help="数据来源: excel（默认）或 mysql",
    )
    parser.addoption(
        "--suite-id",
        action="store",
        default=None,
        type=int,
        help="MySQL 模式下的套件ID（为空则执行所有启用用例）",
    )


@pytest.fixture(scope="session")
def config():
    """加载项目配置"""
    config_path = os.path.join(BASE_DIR, "config", "config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="session")
def active_env(config, request):
    """
    解析当前生效的环境名称。
    优先级：命令行 --env 参数 > 环境变量 PLATFORM_ENV > config.yaml 中的 active_env 字段
    """
    env_from_cli = request.config.getoption("--env")
    env_from_os = os.environ.get("PLATFORM_ENV")
    env_name = env_from_cli or env_from_os or config.get("active_env")

    if not env_name:
        raise ValueError("未指定运行环境，请在 config.yaml 中设置 active_env，或使用 --env 参数")

    environments = config.get("environments", {})
    if env_name not in environments:
        available = list(environments.keys())
        raise ValueError(
            f"环境名称 '{env_name}' 不存在，可用环境: {available}"
        )

    logger.info(f"当前运行环境: {env_name} -> {environments[env_name]['base_url']}")
    return env_name


@pytest.fixture(scope="session")
def env_config(config, active_env):
    """获取当前环境的配置（base_url 等）"""
    return config["environments"][active_env]


@pytest.fixture(scope="session")
def http_client(config, env_config):
    """全局 HTTP 客户端，自动使用当前环境的 base_url"""
    client = HttpClient(
        base_url=env_config.get("base_url", ""),
        timeout=config.get("timeout", 30),
    )
    yield client
    client.close()


@pytest.fixture(scope="session")
def test_data(request):
    """
    测试数据 fixture —— 支持两种数据源，测试代码无需修改

    数据来源由 --source 参数或 PLATFORM_SOURCE 环境变量决定：
      - excel（默认）: 从 test_data/ 目录扫描所有 Excel 文件
      - mysql: 从数据库读取（可配合 --suite-id 指定套件）
    """
    source = request.config.getoption("--source") or os.environ.get("PLATFORM_SOURCE", "excel")
    suite_id = request.config.getoption("--suite-id") or os.environ.get("PLATFORM_SUITE_ID")

    if source == "mysql":
        return _load_from_mysql(suite_id)
    else:
        data_dir = os.path.join(BASE_DIR, "test_data")
        return ExcelReader.load_from_directory(data_dir)


def _load_from_mysql(suite_id=None) -> list[dict]:
    """
    从 MySQL 读取测试用例，返回格式与 ExcelReader 完全一致
    """
    from backend.database import SessionLocal
    from backend.models import TestCase, SuiteCase

    db = SessionLocal()
    try:
        if suite_id:
            suite_id = int(suite_id)
            case_ids = [
                link.case_id for link in
                db.query(SuiteCase).filter(SuiteCase.suite_id == suite_id).order_by(SuiteCase.sort_order).all()
            ]
            cases = db.query(TestCase).filter(TestCase.id.in_(case_ids), TestCase.is_active == True).all()
        else:
            cases = db.query(TestCase).filter(TestCase.is_active == True).order_by(TestCase.sort_order).all()

        result = []
        for c in cases:
            result.append({
                "name": c.name,
                "method": c.method,
                "path": c.path,
                "headers": c.headers,
                "body": c.body,
                "expected_status": c.expected_status or 200,
                "expected_fields": c.expected_fields,
                "_file": f"mysql_case_{c.id}",
                "_sheet": c.module or "default",
            })

        logger.info(f"[MySQL] 共加载 {len(result)} 条用例 (suite_id={suite_id})")
        return result
    finally:
        db.close()
