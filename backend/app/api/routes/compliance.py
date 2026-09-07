"""合规检查路由：GDPR / 数据安全法 / 个人信息保护法视角的条款检查。"""
from fastapi import APIRouter, Depends

from app import models
from app.api.deps import get_current_user
from app.core.database import get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix="/compliance", tags=["合规检查"])


@router.post("/{contract_id}")
def compliance_check(
    contract_id: int,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.services.review_service import review_contract

    contract = (
        db.query(models.Contract)
        .filter_by(id=contract_id, owner_id=user.id)
        .first()
    )
    if not contract:
        from fastapi import HTTPException

        raise HTTPException(404, "合同不存在")
    # 合规检查 = 审查服务的 compliance 模式（限定法规库检索）
    return review_contract(db, contract, review_type="compliance")
