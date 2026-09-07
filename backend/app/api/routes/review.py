"""合同审查路由：风险审查 / 历史报告。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models
from app.api.deps import get_current_user
from app.core.database import get_db
from app.services.review_service import serialize_report

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
    """执行风险审查。review_type: risk / compliance（延迟导入避免启动时加载重依赖）。"""
    from app.services.review_service import review_contract as run

    contract = _get_owned_contract(db, user, contract_id)
    if review_type not in ("risk", "compliance"):
        raise HTTPException(400, "review_type 仅支持 risk / compliance")
    return run(db, contract, review_type)


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
