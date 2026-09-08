"""核心服务：合同风险审查 / 合规检查。

链路：合同正文 -> 按条款切分 -> 逐条混合检索（条款库+法规库）->
    LLM 按审查清单分析 -> 结构化 JSON -> 落库为报告。

性能：检索串行（快）、LLM 调用并发（慢，6 并发），避免长合同逐条串行审查耗时过久。

防幻觉三重约束（面试核心讲点）：
1. Prompt 强制 legal_basis 引用检索到的依据
2. JSON 输出解析失败/格式非法时降级为空，而不是硬编一条
3. 每条风险绑定具体条款号（clause_no），前端可回溯原文
"""
import json
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from uuid import uuid4

from fastapi import HTTPException

from app import models
from app.core.database import SessionLocal
from app.prompts.review_prompt import (
    COMPLIANCE_SYSTEM_PROMPT,
    REVIEW_SYSTEM_PROMPT,
    build_review_user_prompt,
)
from app.rag.retriever import get_retriever
from app.rag.splitter import split_contract
from app.services.llm import get_llm

RISK_ORDER = {"高": 3, "中": 2, "低": 1}

# 审查任务进度表（内存态，进程重启即清空；key = task_id）
_TASKS = {}
_TASKS_LOCK = threading.Lock()


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


def _review_single(clause: dict, refs, llm, system: str) -> list:
    """审查单个条款：LLM 调用 + 结构化解析，返回 risk_items 列表。"""
    user_prompt = build_review_user_prompt(
        clause["clause_no"], clause["content"], _format_refs(refs)
    )
    resp = llm.invoke([("system", system), ("human", user_prompt)])

    items = []
    for r in _parse_json_array(resp.content):
        if not isinstance(r, dict) or not r.get("description"):
            continue
        items.append(
            {
                "clause_no": clause["clause_no"],
                "risk_level": str(r.get("risk_level", "低"))[:10],
                "title": str(r.get("title", "未命名风险"))[:200],
                "description": str(r.get("description", ""))[:2000],
                "suggestion": str(r.get("suggestion", ""))[:2000],
                "legal_basis": str(r.get("legal_basis", ""))[:1000],
            }
        )
    return items


def _update_task(task_id: str, **kwargs):
    with _TASKS_LOCK:
        _TASKS[task_id].update(kwargs)


def start_review(contract_id: int, user_id: int, review_type: str) -> str:
    """创建审查任务，后台异步执行，立即返回 task_id。"""
    task_id = uuid4().hex
    _TASKS[task_id] = {
        "task_id": task_id,
        "status": "running",
        "total": 0,
        "done": 0,
        "current": "",
        "overall_risk": None,
        "result": None,
        "error": None,
    }
    threading.Thread(
        target=_run_review, args=(task_id, contract_id, user_id, review_type), daemon=True
    ).start()
    return task_id


def _run_review(task_id: str, contract_id: int, user_id: int, review_type: str):
    """后台执行审查。注意：后台线程独立创建 db session，不能共享请求线程的 session。"""
    db = SessionLocal()
    try:
        contract = (
            db.query(models.Contract)
            .filter_by(id=contract_id, owner_id=user_id)
            .first()
        )
        if not contract:
            _update_task(task_id, status="error", error="合同不存在")
            return
        if not contract.versions:
            _update_task(task_id, status="error", error="该合同没有正文内容")
            return

        clauses = [c for c in split_contract(contract.versions[-1].content) if len(c["content"]) >= 10]
        if not clauses:
            _update_task(task_id, status="error", error="合同正文为空，无法审查")
            return

        _update_task(task_id, total=len(clauses))

        retriever = get_retriever()
        llm = get_llm(temperature=0.1)
        system = REVIEW_SYSTEM_PROMPT if review_type == "risk" else COMPLIANCE_SYSTEM_PROMPT
        source_type = None if review_type == "risk" else "regulation"

        # 第一步：串行检索（快），避免并发共享向量检索器的线程安全问题
        refs_map = {}
        for cl in clauses:
            refs_map[cl["clause_no"]] = retriever.retrieve(
                cl["content"], top_k=3, source_type=source_type
            )

        # 第二步：并发 LLM 调用（慢），6 个并发显著缩短长合同审查耗时
        risk_items = []
        done = 0
        with ThreadPoolExecutor(max_workers=6) as pool:
            futures = {
                pool.submit(_review_single, cl, refs_map[cl["clause_no"]], llm, system): cl
                for cl in clauses
            }
            for fut in as_completed(futures):
                cl = futures[fut]
                try:
                    risk_items.extend(fut.result())
                except Exception:
                    # 单条失败不影响整体，其余条款继续
                    pass
                done += 1
                _update_task(task_id, done=done, current=cl["clause_no"])

        overall = (
            "无风险"
            if not risk_items
            else max((i["risk_level"] for i in risk_items), key=lambda x: RISK_ORDER.get(x, 0))
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
        _update_task(
            task_id, status="done", overall_risk=overall, result=serialize_report(report)
        )
    except Exception as e:  # noqa: BLE001
        _update_task(task_id, status="error", error=str(e))
    finally:
        db.close()


def get_progress(task_id: str) -> dict:
    """查询审查任务进度。不存在返回 None。"""
    with _TASKS_LOCK:
        return _TASKS.get(task_id)


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
