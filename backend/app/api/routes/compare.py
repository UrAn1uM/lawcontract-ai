"""条款比对路由：直接贴文本比对 / 同一合同的版本间比对。"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app import models
from app.api.deps import get_current_user
from app.core.database import get_db

router = APIRouter(prefix="/compare", tags=["条款比对"])


class CompareTextIn(BaseModel):
    text_a: str
    text_b: str


class CompareVersionIn(BaseModel):
    contract_id: int
    version_a: int
    version_b: int


@router.post("/text")
def compare_text(data: CompareTextIn, user: models.User = Depends(get_current_user)):
    """我方与对方文本直接比对（粘贴两份合同正文）。"""
    if not data.text_a.strip() or not data.text_b.strip():
        raise HTTPException(400, "两份合同文本都不能为空")
    from app.services.compare_service import compare_texts

    return compare_texts(data.text_a, data.text_b)


@router.post("/versions")
def compare_versions(
    data: CompareVersionIn,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """同一合同的两个版本比对（如我方草稿 vs 对方回签版）。"""
    contract = (
        db.query(models.Contract)
        .filter_by(id=data.contract_id, owner_id=user.id)
        .first()
    )
    if not contract:
        raise HTTPException(404, "合同不存在")

    versions = {v.version_no: v.content for v in contract.versions}
    if data.version_a not in versions or data.version_b not in versions:
        raise HTTPException(400, f"版本不存在，现有版本：{sorted(versions)}")

    from app.services.compare_service import compare_texts

    return compare_texts(versions[data.version_a], versions[data.version_b])
