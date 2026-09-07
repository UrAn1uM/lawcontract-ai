"""知识库管理路由：条款库 / 法规库 CRUD + 向量索引重建（管理员）。"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app import models
from app.api.deps import require_admin
from app.core.database import get_db

router = APIRouter(prefix="/knowledge", tags=["知识库管理"])


# ---------- Pydantic 入参 ----------

class ClauseIn(BaseModel):
    title: str
    category: str = "通用"
    risk_level: str = "低"
    content: str
    source: str = "自定义"


class RegulationIn(BaseModel):
    name: str
    article_no: str
    jurisdiction: str = "中国"
    content: str
    effective_date: str = ""


# ---------- 条款库 ----------

@router.get("/clauses")
def list_clauses(db: Session = Depends(get_db)):
    clauses = db.query(models.Clause).order_by(models.Clause.id.desc()).all()
    return [
        {
            "id": c.id,
            "title": c.title,
            "category": c.category,
            "risk_level": c.risk_level,
            "content": c.content,
            "source": c.source,
        }
        for c in clauses
    ]


@router.post("/clauses")
def add_clause(data: ClauseIn, admin: models.User = Depends(require_admin), db: Session = Depends(get_db)):
    clause = models.Clause(**data.model_dump())
    db.add(clause)
    db.commit()
    return {"id": clause.id, "message": "已添加，记得重建向量索引"}


@router.put("/clauses/{clause_id}")
def update_clause(
    clause_id: int,
    data: ClauseIn,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    clause = db.get(models.Clause, clause_id)
    if not clause:
        raise HTTPException(404, "条款不存在")
    for k, v in data.model_dump().items():
        setattr(clause, k, v)
    db.commit()
    return {"message": "已更新，记得重建向量索引"}


@router.delete("/clauses/{clause_id}")
def delete_clause(
    clause_id: int, admin: models.User = Depends(require_admin), db: Session = Depends(get_db)
):
    clause = db.get(models.Clause, clause_id)
    if not clause:
        raise HTTPException(404, "条款不存在")
    db.delete(clause)
    db.commit()
    return {"message": "已删除，记得重建向量索引"}


# ---------- 法规库 ----------

@router.get("/regulations")
def list_regulations(db: Session = Depends(get_db)):
    regs = db.query(models.Regulation).order_by(models.Regulation.id.desc()).all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "article_no": r.article_no,
            "jurisdiction": r.jurisdiction,
            "content": r.content,
            "effective_date": r.effective_date,
        }
        for r in regs
    ]


@router.post("/regulations")
def add_regulation(
    data: RegulationIn, admin: models.User = Depends(require_admin), db: Session = Depends(get_db)
):
    reg = models.Regulation(**data.model_dump())
    db.add(reg)
    db.commit()
    return {"id": reg.id, "message": "已添加，记得重建向量索引"}


@router.put("/regulations/{reg_id}")
def update_regulation(
    reg_id: int,
    data: RegulationIn,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    reg = db.get(models.Regulation, reg_id)
    if not reg:
        raise HTTPException(404, "法规不存在")
    for k, v in data.model_dump().items():
        setattr(reg, k, v)
    db.commit()
    return {"message": "已更新，记得重建向量索引"}


@router.delete("/regulations/{reg_id}")
def delete_regulation(
    reg_id: int, admin: models.User = Depends(require_admin), db: Session = Depends(get_db)
):
    reg = db.get(models.Regulation, reg_id)
    if not reg:
        raise HTTPException(404, "法规不存在")
    db.delete(reg)
    db.commit()
    return {"message": "已删除，记得重建向量索引"}


# ---------- 索引重建 ----------

@router.post("/rebuild-index")
def rebuild_index(admin: models.User = Depends(require_admin), db: Session = Depends(get_db)):
    from app.rag.ingestion import rebuild_index as run

    return run(db)
