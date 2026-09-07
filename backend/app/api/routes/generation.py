"""标准合同生成路由。"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app import models
from app.api.deps import get_current_user
from app.core.database import get_db

router = APIRouter(prefix="/generation", tags=["合同生成"])


class GenerateIn(BaseModel):
    contract_type: str = "服务合同"
    party_a: str = ""
    party_b: str = ""
    subject: str = ""          # 标的/服务内容
    amount: str = ""           # 价款
    duration: str = ""         # 期限
    payment_terms: str = ""    # 付款方式
    special: str = ""          # 特殊约定


@router.post("/contract")
def generate(
    data: GenerateIn,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.services.generation_service import generate_contract

    return generate_contract(db, data.model_dump(), user)
