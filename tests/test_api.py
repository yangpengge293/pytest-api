import json
import os
import pytest
import allure
from utils.excel_reader import ExcelReader
from utils.logger import logger

# test_data 目录路径
TEST_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "test_data")


def load_test_cases():
    """
    加载测试数据 —— 支持两种来源（测试代码无需任何修改）：
    1. Excel 模式（默认）：扫描 test_data/ 下所有 .xlsx 文件的所有 Sheet
    2. MySQL 模式：设置环境变量 PLATFORM_SOURCE=mysql 后从数据库读取
    """
    source = os.environ.get("PLATFORM_SOURCE", "excel")

    if source == "mysql":
        from backend.database import SessionLocal
        from backend.models import TestCase, SuiteCase
        suite_id = os.environ.get("PLATFORM_SUITE_ID")
        db = SessionLocal()
        try:
            if suite_id:
                case_ids = [
                    lc.case_id for lc in
                    db.query(SuiteCase).filter(SuiteCase.suite_id == int(suite_id)).order_by(SuiteCase.sort_order).all()
                ]
                cases = db.query(TestCase).filter(TestCase.id.in_(case_ids), TestCase.is_active == True).all()
            else:
                cases = db.query(TestCase).filter(TestCase.is_active == True).order_by(TestCase.sort_order).all()
            result = []
            for c in cases:
                result.append({
                    "name": c.name, "method": c.method, "path": c.path,
                    "headers": c.headers, "body": c.body,
                    "expected_status": c.expected_status or 200,
                    "expected_fields": c.expected_fields,
                    "_file": f"mysql_case_{c.id}", "_sheet": c.module or "default",
                })
            logger.info(f"[MySQL] 加载 {len(result)} 条用例")
            return result
        finally:
            db.close()
    else:
        return ExcelReader.load_from_directory(TEST_DATA_DIR)


# 模块加载时读取所有数据，用于参数化
test_cases = load_test_cases()


def _make_test_id(case: dict, index: int) -> str:
    """生成可读的测试 ID: Sheet名__用例名"""
    sheet = case.get("_sheet", "unknown")
    name = case.get("name", f"case_{index}")
    return f"{sheet}__{name}"


@allure.feature("接口自动化测试")
class TestApiFromExcel:
    """
    基于 Excel 数据的接口自动化测试

    数据来源：test_data/ 目录下所有 .xlsx 文件的所有 Sheet。
    Allure 报告中按 Sheet 名称分组展示（feature），并标注来源文件（tag）。
    """

    @pytest.mark.parametrize(
        "case",
        test_cases,
        ids=[_make_test_id(c, i) for i, c in enumerate(test_cases)],
    )
    def test_api(self, http_client, case):
        """
        通用接口测试：自动扫描 test_data/ 下所有 Excel 文件、所有 Sheet，逐条执行测试

        Excel 列说明:
        - 用例名称: 测试用例名称
        - 请求方法: GET/POST/PUT/DELETE 等
        - 请求路径: 接口路径
        - 请求头: JSON 格式的请求头
        - 请求参数: JSON 格式的请求参数 (GET 为 query params, POST/PUT 为 body)
        - 预期状态码: 期望的 HTTP 状态码
        - 预期响应字段: JSON 格式，校验响应体中是否包含指定字段和值
        """
        name = case.get("name", "未命名")
        method = case.get("method", "GET")
        path = case.get("path", "/")
        headers_str = case.get("headers")
        body_str = case.get("body")
        expected_status = case.get("expected_status", 200)
        expected_fields_str = case.get("expected_fields")
        source_file = case.get("_file", "")
        source_sheet = case.get("_sheet", "")

        # Allure 报告：按 Sheet 分组，标注来源文件
        allure.dynamic.title(name)
        allure.dynamic.story(f"{method} {path}")
        allure.dynamic.feature(source_sheet or "接口自动化测试")
        allure.dynamic.tag(source_file)
        logger.info(f"===== 执行用例: [{source_file} / {source_sheet}] {name} =====")

        # 解析请求头和请求参数
        headers = ExcelReader.parse_json_field(headers_str)
        body = ExcelReader.parse_json_field(body_str)

        # 对于 GET 请求，参数作为 query params；其他请求作为 JSON body
        params = None
        json_data = None
        if method.upper() == "GET":
            params = body
        else:
            json_data = body

        # 发送请求
        response = http_client.request(
            method=method,
            path=path,
            headers=headers,
            params=params,
            json_data=json_data,
        )

        # 断言状态码
        assert response.status_code == expected_status, (
            f"状态码不匹配: 期望 {expected_status}, 实际 {response.status_code}"
        )

        # 断言响应字段
        expected_fields = ExcelReader.parse_json_field(expected_fields_str)
        if expected_fields:
            resp_json = response.json()
            for key, value in expected_fields.items():
                assert key in resp_json, f"响应中缺少字段: {key}"
                assert resp_json[key] == value, (
                    f"字段 {key} 值不匹配: 期望 {value}, 实际 {resp_json[key]}"
                )
