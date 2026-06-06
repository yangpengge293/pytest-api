import os
import pytest
import yaml
from utils.http_client import HttpClient
from utils.excel_reader import ExcelReader

# 项目根目录
BASE_DIR = os.path.dirname(__file__)


@pytest.fixture(scope="session")
def config():
    """加载项目配置"""
    config_path = os.path.join(BASE_DIR, "config", "config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="session")
def http_client(config):
    """全局 HTTP 客户端"""
    client = HttpClient(
        base_url=config.get("base_url", ""),
        timeout=config.get("timeout", 30),
    )
    yield client
    client.close()


@pytest.fixture(scope="session")
def test_data():
    """从 Excel 加载测试数据"""
    excel_path = os.path.join(BASE_DIR, "test_data", "test_cases.xlsx")
    reader = ExcelReader(excel_path)
    return reader.read_data()
