"""条款比对服务：文本层 diff + 语义层向量相似度，两层结合。

面试讲点：
- 字面相似度（difflib）回答"改了哪些字"，语义相似度（embedding 余弦）回答"意思变没变"
- "措辞修改"= 字面变了语义没变；"语义修改"= 权利义务实质性变化，需要法务重点关注
"""
import difflib

import numpy as np

from app.rag.embedder import embed_texts
from app.rag.splitter import split_contract


def _cosine(a, b) -> float:
    a, b = np.asarray(a), np.asarray(b)
    denom = float(np.linalg.norm(a) * np.linalg.norm(b)) or 1.0
    return float(np.dot(a, b) / denom)


def compare_texts(text_a: str, text_b: str) -> dict:
    clauses_a = split_contract(text_a)
    clauses_b = split_contract(text_b)
    diffs = []
    used_b = set()

    for ca in clauses_a:
        # 用序列匹配在 B 版本中找最相近条款（对齐）
        best_j, best_ratio = None, 0.0
        for j, cb in enumerate(clauses_b):
            if j in used_b:
                continue
            ratio = difflib.SequenceMatcher(None, ca["content"], cb["content"]).ratio()
            if ratio > best_ratio:
                best_j, best_ratio = j, ratio

        if best_j is None or best_ratio < 0.35:
            diffs.append(
                {
                    "type": "删除",
                    "a_no": ca["clause_no"],
                    "a_content": ca["content"][:500],
                    "b_no": "",
                    "b_content": "",
                    "text_similarity": round(best_ratio, 3),
                    "semantic_change": 1.0,
                }
            )
            continue

        used_b.add(best_j)
        cb = clauses_b[best_j]
        if best_ratio >= 0.98:
            change_type, semantic_change = "未变", 0.0
        else:
            va, vb = embed_texts([ca["content"], cb["content"]])
            semantic_change = round(1 - _cosine(va, vb), 3)
            change_type = "语义修改" if semantic_change > 0.15 else "措辞修改"
        diffs.append(
            {
                "type": change_type,
                "a_no": ca["clause_no"],
                "a_content": ca["content"][:500],
                "b_no": cb["clause_no"],
                "b_content": cb["content"][:500],
                "text_similarity": round(best_ratio, 3),
                "semantic_change": semantic_change,
            }
        )

    for j, cb in enumerate(clauses_b):
        if j not in used_b:
            diffs.append(
                {
                    "type": "新增",
                    "a_no": "",
                    "a_content": "",
                    "b_no": cb["clause_no"],
                    "b_content": cb["content"][:500],
                    "text_similarity": 0.0,
                    "semantic_change": 1.0,
                }
            )

    summary = {t: 0 for t in ("新增", "删除", "语义修改", "措辞修改", "未变")}
    for d in diffs:
        summary[d["type"]] = summary.get(d["type"], 0) + 1
    return {"summary": summary, "diffs": diffs}
