"""标准合同生成服务：要素问答 -> LLM 起草 -> 规则自检 -> 落库。"""
from app import models
from app.prompts.generation_prompt import GENERATION_SYSTEM_PROMPT, SELF_CHECK_KEYWORDS
from app.services.llm import get_llm


def generate_contract(db, answers: dict, user: models.User) -> dict:
    fields = "\n".join(
        f"- {k}：{v}" for k, v in answers.items() if v and str(v).strip()
    )
    if not fields:
        fields = "-（用户未提供要素，请生成通用模板并用【待填写】标注）"

    llm = get_llm(temperature=0.3)
    text = llm.invoke(
        [
            ("system", GENERATION_SYSTEM_PROMPT),
            ("human", f"请根据以下合同要素起草合同：\n{fields}"),
        ]
    ).content

    # 自检闭环：规则层确定性校验必备条款（不依赖大模型，保证下限）
    missing = [kw for kw in SELF_CHECK_KEYWORDS if kw not in text]
    self_check = {
        "passed": not missing,
        "missing": missing,
        "message": "必备条款齐全" if not missing else f"缺少必备条款：{'、'.join(missing)}",
    }

    contract = models.Contract(
        owner_id=user.id,
        title=f"生成的{answers.get('contract_type', '')}合同",
        contract_type=answers.get("contract_type", "其他"),
        status="generated",
    )
    db.add(contract)
    db.flush()
    db.add(models.ContractVersion(contract_id=contract.id, version_no=1, content=text))
    db.commit()

    return {"contract_id": contract.id, "contract_text": text, "self_check": self_check}
