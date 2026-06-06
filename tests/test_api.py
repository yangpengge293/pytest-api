import json
import pytest
import allure
from utils.excel_reader import ExcelReader
from utils.logger import logger


def load_test_cases():
    """加载 Excel 测试数据，供 pytest.mark.parametrize 使用"""
    import os
    excel_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "test_data", "test_cases.xlsx"
    )
    reader = ExcelReader(excel_path)
    return reader.read_data()


# 在模块加载时读取数据，用于参数化
test_cases = load_test_cases()


@allure.feature("接口自动化测试")
class TestApiFromExcel:
    """基于 Excel 数据的接口自动化测试"""

    @pytest.mark.parametrize(
        "case",
        test_cases,
        ids=[c.get("name", f"case_{i}") for i, c in enumerate(test_cases)],
    )
    def test_api(self, http_client, case):
        """
        通用接口测试：根据 Excel 中的数据逐条执行测试

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

        allure.dynamic.title(name)
        allure.dynamic.story(f"{method} {path}")
        logger.info(f"===== 执行用例: {name} =====")

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
