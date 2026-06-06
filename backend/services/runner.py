"""
测试执行引擎
====================
核心：完全复用 utils/http_client.py 的 HttpClient 和 test_api.py 的断言逻辑，
     只是数据来源从 Excel 切换为 MySQL，结果回写到数据库。

三种触发方式统一走这个引擎：
  1. 页面手动点击  -> Celery task  -> run_suite()
  2. 定时回归       -> Celery beat -> run_suite()
  3. CI 触发        -> API 调用    -> Celery task -> run_suite()
"""
import json
import time
import os
import traceback
from datetime import datetime

import yaml

from backend.config import settings
from backend.database import SessionLocal
from backend.models import TestCase, TestSuite, SuiteCase, Execution, TestResult
from utils.http_client import HttpClient  # ← 复用现有 HttpClient
from utils.logger import logger


def _load_project_config() -> dict:
    """加载 config/config.yaml"""
    config_path = os.path.join(
        settings.PROJECT_ROOT or os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "config", "config.yaml",
    )
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _resolve_base_url(env: str) -> tuple[str, int]:
    """根据环境名解析 base_url 和 timeout"""
    cfg = _load_project_config()
    environments = cfg.get("environments", {})
    if env not in environments:
        available = list(environments.keys())
        raise ValueError(f"环境 '{env}' 不存在，可用: {available}")
    base_url = environments[env]["base_url"]
    timeout = cfg.get("timeout", 30)
    return base_url, timeout


def _parse_json(field: str | None) -> dict | None:
    """与 ExcelReader.parse_json_field 相同的逻辑"""
    if not field or str(field).strip() == "":
        return None
    try:
        return json.loads(str(field))
    except json.JSONDecodeError:
        return None


def _get_cases_for_suite(db, suite_id: int | None) -> list[TestCase]:
    """获取待执行的用例列表"""
    if suite_id:
        case_ids = [
            link.case_id for link in
            db.query(SuiteCase).filter(SuiteCase.suite_id == suite_id).order_by(SuiteCase.sort_order).all()
        ]
        if not case_ids:
            return []
        return db.query(TestCase).filter(TestCase.id.in_(case_ids), TestCase.is_active == True).all()
    else:
        return db.query(TestCase).filter(TestCase.is_active == True).order_by(TestCase.sort_order, TestCase.id).all()


def _execute_single_case(client: HttpClient, case: TestCase) -> dict:
    """
    执行单条用例 —— 断言逻辑完全复用 test_api.py 的 test_api 方法
    返回结果字典
    """
    result = {
        "case_id": case.id,
        "case_name": case.name,
        "method": case.method,
        "path": case.path,
        "status": "passed",
        "actual_status_code": None,
        "actual_response": None,
        "error_message": None,
        "duration_ms": 0,
    }

    start = time.time()
    try:
        headers = _parse_json(case.headers)
        body = _parse_json(case.body)
        expected_status = case.expected_status or 200

        # 与 test_api.py 完全一致的请求逻辑
        params = None
        json_data = None
        if case.method.upper() == "GET":
            params = body
        else:
            json_data = body

        response = client.request(
            method=case.method,
            path=case.path,
            headers=headers,
            params=params,
            json_data=json_data,
        )

        result["actual_status_code"] = response.status_code

        # 截断保存响应体
        try:
            resp_text = json.dumps(response.json(), ensure_ascii=False)
            result["actual_response"] = resp_text[:2000]
        except Exception:
            result["actual_response"] = response.text[:2000]

        # 断言状态码 —— 与 test_api.py 一致
        assert response.status_code == expected_status, (
            f"状态码不匹配: 期望 {expected_status}, 实际 {response.status_code}"
        )

        # 断言响应字段 —— 与 test_api.py 一致
        expected_fields = _parse_json(case.expected_fields)
        if expected_fields:
            resp_json = response.json()
            for key, value in expected_fields.items():
                assert key in resp_json, f"响应中缺少字段: {key}"
                assert resp_json[key] == value, (
                    f"字段 {key} 值不匹配: 期望 {value}, 实际 {resp_json[key]}"
                )

    except AssertionError as e:
        result["status"] = "failed"
        result["error_message"] = str(e)
    except Exception as e:
        result["status"] = "error"
        result["error_message"] = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"
    finally:
        result["duration_ms"] = int((time.time() - start) * 1000)

    return result


def run_suite(execution_id: int, suite_id: int | None, env: str):
    """
    执行套件：从 MySQL 读取用例 → 用 HttpClient 发送请求 → 结果写回 MySQL
    """
    db = SessionLocal()
    record = None
    try:
        record = db.query(Execution).get(execution_id)
        if not record:
            logger.error(f"执行记录 {execution_id} 不存在")
            return

        # 更新状态为 running
        record.status = "running"
        record.started_at = datetime.now()
        db.commit()

        # 获取待执行用例
        cases = _get_cases_for_suite(db, suite_id)
        record.total = len(cases)
        db.commit()

        if not cases:
            record.status = "passed"
            record.finished_at = datetime.now()
            db.commit()
            logger.warning(f"执行记录 {execution_id} 无可用用例")
            return

        # 创建 HttpClient（复用现有类）
        base_url, timeout = _resolve_base_url(env)
        client = HttpClient(base_url=base_url, timeout=timeout)
        logger.info(f"开始执行: execution_id={execution_id}, env={env}, url={base_url}, 用例数={len(cases)}")

        passed, failed, error = 0, 0, 0
        try:
            for case in cases:
                result_data = _execute_single_case(client, case)

                # 保存单条结果到数据库
                db_result = TestResult(
                    execution_id=execution_id,
                    case_id=result_data["case_id"],
                    case_name=result_data["case_name"],
                    method=result_data["method"],
                    path=result_data["path"],
                    status=result_data["status"],
                    actual_status_code=result_data["actual_status_code"],
                    actual_response=result_data["actual_response"],
                    error_message=result_data["error_message"],
                    duration_ms=result_data["duration_ms"],
                )
                db.add(db_result)

                if result_data["status"] == "passed":
                    passed += 1
                elif result_data["status"] == "failed":
                    failed += 1
                else:
                    error += 1

                # 实时更新计数
                record.passed = passed
                record.failed = failed
                record.error = error
                db.commit()

        finally:
            client.close()

        # 最终状态
        record.finished_at = datetime.now()
        duration_sec = (record.finished_at - record.started_at).total_seconds()
        record.duration = f"{duration_sec:.2f}s"
        if failed > 0 or error > 0:
            record.status = "failed"
        else:
            record.status = "passed"

        db.commit()
        logger.info(
            f"执行完成: execution_id={execution_id}, "
            f"total={record.total}, passed={passed}, failed={failed}, error={error}"
        )

    except Exception as e:
        logger.error(f"执行异常: {e}\n{traceback.format_exc()}")
        if record:
            record.status = "error"
            record.error_message = str(e)
            record.finished_at = datetime.now()
            db.commit()
    finally:
        db.close()
