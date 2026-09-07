"""合同管理路由：上传解析 / 列表 / 详情 / 新版本。"""
import os
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app import models
from app.api.deps import get_current_user
from app.core.database import get_db
from app.services.document_parser import parse_document

router = APIRouter(prefix="/contracts", tags=["合同管理"])

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
ALLOWED_EXT = (".docx", ".pdf", ".txt")


def _get_owned_contract(db, user, contract_id) -> models.Contract:
    contract = (
        db.query(models.Contract)
        .filter_by(id=contract_id, owner_id=user.id)
        .first()
    )
    if not contract:
        raise HTTPException(404, "合同不存在")
    return contract


@router.post("/upload")
def upload_contract(
    file: UploadFile = File(...),
    title: str = Form(None),
    contract_type: str = Form("其他"),
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not file.filename.lower().endswith(ALLOWED_EXT):
        raise HTTPException(400, "仅支持 docx / pdf / txt 格式")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    dest = os.path.join(UPLOAD_DIR, f"{uuid4().hex}_{file.filename}")
    with open(dest, "wb") as f:
        f.write(file.file.read())

    try:
        text = parse_document(dest)
    except Exception:
        raise HTTPException(400, "文件解析失败，请确认文件未损坏（扫描件 PDF 暂不支持）")
    if not text.strip():
        raise HTTPException(400, "未解析到文本内容")

    contract = models.Contract(
        owner_id=user.id,
        title=title or os.path.splitext(file.filename)[0],
        contract_type=contract_type,
    )
    db.add(contract)
    db.flush()
    db.add(models.ContractVersion(contract_id=contract.id, version_no=1, content=text))
    db.commit()
    return {"id": contract.id, "title": contract.title, "version_no": 1}


@router.get("")
def list_contracts(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    contracts = (
        db.query(models.Contract)
        .filter_by(owner_id=user.id)
        .order_by(models.Contract.id.desc())
        .all()
    )
    return [
        {
            "id": c.id,
            "title": c.title,
            "contract_type": c.contract_type,
            "status": c.status,
            "version_count": len(c.versions),
            "created_at": str(c.created_at or ""),
        }
        for c in contracts
    ]


@router.get("/{contract_id}")
def get_contract(
    contract_id: int,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    contract = _get_owned_contract(db, user, contract_id)
    version = contract.versions[-1] if contract.versions else None
    return {
        "id": contract.id,
        "title": contract.title,
        "contract_type": contract.contract_type,
        "status": contract.status,
        "versions": [
            {"id": v.id, "version_no": v.version_no, "created_at": str(v.created_at or "")}
            for v in contract.versions
        ],
        "content": version.content if version else "",
    }


@router.post("/{contract_id}/versions")
def upload_new_version(
    contract_id: int,
    file: UploadFile = File(...),
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """上传新版本（对方回签版 / 修订版），供条款比对使用。"""
    contract = _get_owned_contract(db, user, contract_id)
    if not file.filename.lower().endswith(ALLOWED_EXT):
        raise HTTPException(400, "仅支持 docx / pdf / txt 格式")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    dest = os.path.join(UPLOAD_DIR, f"{uuid4().hex}_{file.filename}")
    with open(dest, "wb") as f:
        f.write(file.file.read())
    try:
        text = parse_document(dest)
    except Exception:
        raise HTTPException(400, "文件解析失败")
    if not text.strip():
        raise HTTPException(400, "未解析到文本内容")

    next_no = (contract.versions[-1].version_no if contract.versions else 0) + 1
    db.add(models.ContractVersion(contract_id=contract.id, version_no=next_no, content=text))
    db.commit()
    return {"contract_id": contract.id, "version_no": next_no}
