"""知识库向量化入库：把 MySQL 里的条款库 + 法规库全量灌入向量库。"""
from fastapi import HTTPException

from app import models
from app.rag.retriever import reset_retriever
from app.rag.vector_store import VectorStore


def rebuild_index(db) -> dict:
    """全量重建向量索引。调用场景：种子数据导入后 / 知识库内容变更后。"""
    clauses = db.query(models.Clause).all()
    regulations = db.query(models.Regulation).all()

    texts, metadatas = [], []
    for c in clauses:
        texts.append(c.content)
        metadatas.append({
            "type": "clause",
            "ref_id": c.id,
            "title": c.title,
            "category": c.category,
            "risk_level": c.risk_level,
        })
    for r in regulations:
        texts.append(r.content)
        metadatas.append({
            "type": "regulation",
            "ref_id": r.id,
            "name": r.name,
            "article": r.article_no,
            "jurisdiction": r.jurisdiction,
        })

    if not texts:
        raise HTTPException(400, "知识库为空：请先添加标准条款或法规条文")

    store = VectorStore().build(texts, metadatas)
    store.save()
    reset_retriever()
    return {"indexed": len(texts), "clauses": len(clauses), "regulations": len(regulations)}
