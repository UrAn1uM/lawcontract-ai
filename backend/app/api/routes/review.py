"""合同审查路由：发起审查 / 进度查询 / 历史报告。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models
from app.api.deps import get_current_user
from app.core.database import get_db
from app.services.review_service import get_progress, serialize_report, start_review

router = APIRouter(prefix="/review", tags=["合同审查"])


def _get_owned_contract(db, user, contract_id) -> models.Contract:
    contract = (
        db.query(models.Contract).filter_by(id=contract_id, owner_id=user.id).first()
    )
    if not contract:
        raise HTTPException(404, "合同不存在")
    return contract


@router.post("/{contract_id}")
def review_contract(
    contract_id: int,
    review_type: str = "risk",
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """发起风险审查，后台异步执行，立即返回 task_id，前端据此轮询进度。"""
    _get_owned_contract(db, user, contract_id)
    if review_type not in ("risk", "compliance"):
        raise HTTPException(400, "review_type 仅支持 risk / compliance")
    task_id = start_review(contract_id, user.id, review_type)
    return {"task_id": task_id}


@router.get("/progress/{task_id}")
def review_progress(
    task_id: str,
    user: models.User = Depends(get_current_user),
):
    """查询审查任务进度：status(running/done/error)、total、done、current、result。"""
    task = get_progress(task_id)
    if not task:
        raise HTTPException(404, "任务不存在或已过期")
    return task


@router.get("/reports/{contract_id}")
def list_reports(
    contract_id: int,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_owned_contract(db, user, contract_id)
    reports = (
        db.query(models.ReviewReport)
        .filter_by(contract_id=contract_id)
        .order_by(models.ReviewReport.id.desc())
        .all()
    )
    return [serialize_report(r) for r in reports]
