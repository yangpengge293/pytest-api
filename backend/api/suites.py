"""
测试套件 CRUD 接口
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import TestSuite, SuiteCase
from backend.schemas import SuiteCreate, SuiteUpdate, SuiteOut, ApiResponse, PageResponse

router = APIRouter(prefix="/suites", tags=["测试套件"])


def _suite_to_dict(suite: TestSuite) -> dict:
    case_ids = [link.case_id for link in sorted(suite.suite_links, key=lambda x: x.sort_order)]
    return {
        "id": suite.id, "name": suite.name, "description": suite.description,
        "env": suite.env, "case_ids": case_ids, "case_count": len(case_ids),
        "created_at": suite.created_at, "updated_at": suite.updated_at,
    }


@router.get("", response_model=PageResponse)
def list_suites(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """分页查询测试套件"""
    total = db.query(TestSuite).count()
    suites = db.query(TestSuite).offset((page - 1) * page_size).limit(page_size).all()
    return PageResponse(
        data=[_suite_to_dict(s) for s in suites],
        total=total, page=page, page_size=page_size,
    )


@router.get("/{suite_id}", response_model=ApiResponse)
def get_suite(suite_id: int, db: Session = Depends(get_db)):
    suite = db.query(TestSuite).get(suite_id)
    if not suite:
        return ApiResponse(code=404, message="套件不存在")
    return ApiResponse(data=_suite_to_dict(suite))


@router.post("", response_model=ApiResponse)
def create_suite(data: SuiteCreate, db: Session = Depends(get_db)):
    """新建套件并关联用例"""
    suite = TestSuite(name=data.name, description=data.description, env=data.env)
    db.add(suite)
    db.flush()
    for i, cid in enumerate(data.case_ids):
        db.add(SuiteCase(suite_id=suite.id, case_id=cid, sort_order=i))
    db.commit()
    db.refresh(suite)
    return ApiResponse(data=_suite_to_dict(suite))


@router.put("/{suite_id}", response_model=ApiResponse)
def update_suite(suite_id: int, data: SuiteUpdate, db: Session = Depends(get_db)):
    """更新套件"""
    suite = db.query(TestSuite).get(suite_id)
    if not suite:
        return ApiResponse(code=404, message="套件不存在")
    if data.name is not None:
        suite.name = data.name
    if data.description is not None:
        suite.description = data.description
    if data.env is not None:
        suite.env = data.env
    if data.case_ids is not None:
        db.query(SuiteCase).filter(SuiteCase.suite_id == suite_id).delete()
        for i, cid in enumerate(data.case_ids):
            db.add(SuiteCase(suite_id=suite_id, case_id=cid, sort_order=i))
    db.commit()
    db.refresh(suite)
    return ApiResponse(data=_suite_to_dict(suite))


@router.delete("/{suite_id}", response_model=ApiResponse)
def delete_suite(suite_id: int, db: Session = Depends(get_db)):
    suite = db.query(TestSuite).get(suite_id)
    if not suite:
        return ApiResponse(code=404, message="套件不存在")
    db.delete(suite)
    db.commit()
    return ApiResponse(message="删除成功")
