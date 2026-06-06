import os
from openpyxl import load_workbook
from utils.logger import logger


class ExcelReader:
    """
    Excel 测试数据读取器

    Excel 表格列说明（第一行为表头）：
    | 用例名称 | 请求方法 | 请求路径 | 请求头(JSON) | 请求参数(JSON) | 预期状态码 | 预期响应字段(JSON) |
    """

    # 表头映射
    COLUMN_MAP = {
        "用例名称": "name",
        "请求方法": "method",
        "请求路径": "path",
        "请求头": "headers",
        "请求参数": "body",
        "预期状态码": "expected_status",
        "预期响应字段": "expected_fields",
    }

    def __init__(self, file_path: str, sheet_name: str = None):
        self.file_path = file_path
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Excel 文件不存在: {file_path}")
        self.workbook = load_workbook(file_path, read_only=True)
        self.sheet_name = sheet_name
        self.sheet = self.workbook[sheet_name] if sheet_name else self.workbook.active
        logger.info(f"加载 Excel: {file_path}, Sheet: {self.sheet.title}")

    def read_data(self) -> list[dict]:
        """读取所有测试用例数据，返回字典列表"""
        rows = list(self.sheet.iter_rows(values_only=True))
        if not rows:
            return []

        headers = rows[0]
        # 将中文表头映射为英文字段名
        col_keys = [self.COLUMN_MAP.get(h, h) for h in headers]

        cases = []
        for row in rows[1:]:
            if not any(row):  # 跳过空行
                continue
            case = dict(zip(col_keys, row))
            # 将预期状态码转为整数
            if "expected_status" in case and case["expected_status"]:
                case["expected_status"] = int(case["expected_status"])
            cases.append(case)

        logger.info(f"共读取 {len(cases)} 条测试用例")
        self.workbook.close()
        return cases

    @staticmethod
    def parse_json_field(field: str) -> dict | None:
        """将 JSON 字符串字段解析为字典"""
        import json
        if not field or str(field).strip() == "":
            return None
        try:
            return json.loads(str(field))
        except json.JSONDecodeError as e:
            logger.warning(f"JSON 解析失败: {field}, 错误: {e}")
            return None
