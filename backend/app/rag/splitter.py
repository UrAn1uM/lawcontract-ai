"""合同文本切分：法律文本天然按"第X条"分节，优先保留条款完整性。"""
import re

# 匹配"第一条/第1条/第一百零二条"等条款编号
CLAUSE_PATTERN = re.compile(r"(第[一二三四五六七八九十百千零\d]+条)")


def split_contract(text: str):
    """把合同正文切成 [{"clause_no": "第一条", "content": "..."}]。

    无条款结构时按空行分段兜底，保证任何文本都能进入审查流程。
    """
    text = (text or "").strip()
    if not text:
        return []

    pieces = CLAUSE_PATTERN.split(text)

    # 没匹配到条款编号 -> 按空行分段
    if len(pieces) <= 1:
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        return [
            {"clause_no": f"段落{i}", "content": p}
            for i, p in enumerate(paragraphs, 1)
        ]

    clauses = []
    preamble = pieces[0].strip()
    if preamble:
        clauses.append({"clause_no": "前言", "content": preamble})

    # split 带捕获组的结果：奇数位是编号，偶数位是对应正文
    for i in range(1, len(pieces) - 1, 2):
        no = pieces[i].strip()
        content = (pieces[i + 1] if i + 1 < len(pieces) else "").strip()
        if no or content:
            clauses.append({"clause_no": no, "content": content})
    return clauses
