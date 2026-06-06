"""
测试用例 CRUD 接口
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import TestCase
from backend.schemas import CaseCreate, CaseUpdate, CaseOut, ApiResponse, PageResponse

router = APIRouter(prefix="/cases", tags=["测试用例"])


@router.get("", response_model=PageResponse)
def list_cases(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    module: str | None = None,
    priority: str | None = None,
    keyword: str | None = None,
    db: Session = Depends(get_db),
):
    """分页查询测试用例"""
    query = db.query(TestCase)
    if module:
        query = query.filter(TestCase.module == module)
    if priority:
        query = query.filter(TestCase.priority == priority)
    if keyword:
        query = query.filter(TestCase.name.contains(keyword))

    total = query.count()
    cases = query.order_by(TestCase.sort_order, TestCase.id).offset((page - 1) * page_size).limit(page_size).all()
    return PageResponse(
        data=[CaseOut.model_validate(c).model_dump() for c in cases],
        total=total, page=page, page_size=page_size,
    )


@router.get("/{case_id}", response_model=ApiResponse)
def get_case(case_id: int, db: Session = Depends(get_db)):
    """获取单条用例"""
    case = db.query(TestCase).get(case_id)
    if not case:
        return ApiResponse(code=404, message="用例不存在")
    return ApiResponse(data=CaseOut.model_validate(case).model_dump())


@router.post("", response_model=ApiResponse)
def create_case(data: CaseCreate, db: Session = Depends(get_db)):
    """新建测试用例"""
    case = TestCase(**data.model_dump())
    db.add(case)
    db.commit()
    db.refresh(case)
    return ApiResponse(data=CaseOut.model_validate(case).model_dump())


@router.put("/{case_id}", response_model=ApiResponse)
def update_case(case_id: int, data: CaseUpdate, db: Session = Depends(get_db)):
    """更新测试用例"""
    case = db.query(TestCase).get(case_id)
    if not case:
        return ApiResponse(code=404, message="用例不存在")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(case, field, value)
    db.commit()
    db.refresh(case)
    return ApiResponse(data=CaseOut.model_validate(case).model_dump())


@router.delete("/{case_id}", response_model=ApiResponse)
def delete_case(case_id: int, db: Session = Depends(get_db)):
    """删除测试用例"""
    case = db.query(TestCase).get(case_id)
    if not case:
        return ApiResponse(code=404, message="用例不存在")
    db.delete(case)
    db.commit()
    return ApiResponse(message="删除成功")


@router.post("/batch", response_model=ApiResponse)
def batch_create_cases(data: list[CaseCreate], db: Session = Depends(get_db)):
    """批量导入用例（从页面粘贴或从Excel导入）"""
    cases = [TestCase(**c.model_dump()) for c in data]
    db.add_all(cases)
    db.commit()
    return ApiResponse(message=f"成功导入 {len(cases)} 条用例")


@router.get("/modules/list", response_model=ApiResponse)
def list_modules(db: Session = Depends(get_db)):
    """获取所有模块名（用于筛选）"""
    modules = db.query(TestCase.module).distinct().all()
    return ApiResponse(data=[m[0] for m in modules if m[0]])
