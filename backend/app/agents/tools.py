"""Agent 工具：把 RAG 检索能力注册为 LangChain tool，供问答 Agent 调用。"""
from langchain_core.tools import tool


@tool
def search_clauses(query: str) -> str:
    """检索标准条款库。当用户询问标准条款写法、条款模板、某类条款如何约定时调用。输入为检索关键词。"""
    from app.rag.retriever import get_retriever

    results = get_retriever().retrieve(query, top_k=3, source_type="clause")
    if not results:
        return "未检索到相关标准条款。"
    return "\n\n".join(
        f"【{i + 1}】{meta.get('title', '标准条款')}（分类：{meta.get('category', '通用')}）：\n{text}"
        for i, (text, meta) in enumerate(results)
    )


@tool
def search_regulations(query: str) -> str:
    """检索法规库（数据安全法、个人信息保护法、GDPR 等）。当用户询问法律法规要求、合规义务时调用。输入为检索关键词。"""
    from app.rag.retriever import get_retriever

    results = get_retriever().retrieve(query, top_k=3, source_type="regulation")
    if not results:
        return "未检索到相关法规条文。"
    return "\n\n".join(
        f"【{i + 1}】{meta.get('name', '')}{meta.get('article', '')}：\n{text}"
        for i, (text, meta) in enumerate(results)
    )
