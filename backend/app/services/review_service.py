"""核心服务：合同风险审查 / 合规检查。

链路：合同正文 -> 按条款切分 -> 逐条混合检索（条款库+法规库）->
    LLM 按审查清单分析 -> 结构化 JSON -> 落库为报告。

防幻觉三重约束（面试核心讲点）：
1. Prompt 强制 legal_basis 引用检索到的依据
2. JSON 输出解析失败/格式非法时降级为空，而不是硬编一条
3. 每条风险绑定具体条款号（clause_no），前端可回溯原文
"""
import json
import re

from fastapi import HTTPException

from app import models
from app.prompts.review_prompt import (
    COMPLIANCE_SYSTEM_PROMPT,
    REVIEW_SYSTEM_PROMPT,
    build_review_user_prompt,
)
from app.rag.retriever import get_retriever
from app.rag.splitter import split_contract
from app.services.llm import get_llm

RISK_ORDER = {"高": 3, "中": 2, "低": 1}


def _parse_json_array(text: str) -> list:
    """容错解析 LLM 输出的 JSON 数组：剥掉 markdown 围栏、截取中括号、失败返回 []。"""
    text = re.sub(r"```(json)?", "", (text or "").strip()).strip()
    start, end = text.find("["), text.rfind("]")
    if start == -1 or end <= start:
        return []
    try:
        data = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def _format_refs(refs) -> str:
    if not refs:
        return "（未检索到参考依据）"
    lines = []
    for text, meta in refs:
        label = meta.get("title") or f"{meta.get('name', '')}{meta.get('article', '')}"
        lines.append(f"- [{meta.get('type', '')}][{label}] {text[:200]}")
    return "\n".join(lines)


def review_contract(db, contract: models.Contract, review_type: str = "risk") -> dict:
    """review_type: risk=风险审查, compliance=合规检查（法规库限定检索）。"""
    if not contract.versions:
        raise HTTPException(400, "该合同没有正文内容")

    version = contract.versions[-1]
    clauses = split_contract(version.content)
    if not clauses:
        raise HTTPException(400, "合同正文为空，无法审查")

    retriever = get_retriever()
    llm = get_llm(temperature=0.1)
    system = REVIEW_SYSTEM_PROMPT if review_type == "risk" else COMPLIANCE_SYSTEM_PROMPT
    source_type = None if review_type == "risk" else "regulation"

    risk_items = []
    for cl in clauses:
        # 过短内容（标题、编号行）不值得调用 LLM，直接跳过
        if len(cl["content"]) < 10:
            continue
        refs = retriever.retrieve(cl["content"], top_k=3, source_type=source_type)
        user_prompt = build_review_user_prompt(
            cl["clause_no"], cl["content"], _format_refs(refs)
        )
        try:
            resp = llm.invoke([("system", system), ("human", user_prompt)])
        except ValueError as e:  # 未配置 API Key
            raise HTTPException(400, str(e))

        for r in _parse_json_array(resp.content):
            if not isinstance(r, dict) or not r.get("description"):
                continue
            risk_items.append(
                {
                    "clause_no": cl["clause_no"],
                    "risk_level": str(r.get("risk_level", "低"))[:10],
                    "title": str(r.get("title", "未命名风险"))[:200],
                    "description": str(r.get("description", ""))[:2000],
                    "suggestion": str(r.get("suggestion", ""))[:2000],
                    "legal_basis": str(r.get("legal_basis", ""))[:1000],
                }
            )

    overall = (
        "无风险"
        if not risk_items
        else max(
            (i["risk_level"] for i in risk_items),
            key=lambda x: RISK_ORDER.get(x, 0),
        )
    )
    report = models.ReviewReport(
        contract_id=contract.id,
        review_type=review_type,
        overall_risk=overall,
        summary=f"共识别 {len(risk_items)} 条{'合规问题' if review_type == 'compliance' else '风险'}，整体风险等级：{overall}",
    )
    db.add(report)
    db.flush()
    for it in risk_items:
        db.add(models.RiskItem(report_id=report.id, **it))
    contract.status = "reviewed"
    db.commit()
    db.refresh(report)
    return serialize_report(report)


def serialize_report(report: models.ReviewReport) -> dict:
    return {
        "id": report.id,
        "contract_id": report.contract_id,
        "review_type": report.review_type,
        "overall_risk": report.overall_risk,
        "summary": report.summary,
        "created_at": str(report.created_at or ""),
        "items": [
            {
                "id": item.id,
                "clause_no": item.clause_no,
                "risk_level": item.risk_level,
                "title": item.title,
                "description": item.description,
                "suggestion": item.suggestion,
                "legal_basis": item.legal_basis,
            }
            for item in report.items
        ],
    }
