"""智能问答 Agent：LangChain tool-calling（Agent 决定何时检索条款库/法规库）。

设计说明（面试可讲）：
- 复杂问题走 Agent（自主决定检索哪个库、检索几次）；这类"路由"能力是 Agent 与固定 RAG 链的本质区别
- 简单问答不需要每次都过 Agent——生产上可按意图分流省 token（本项目为教学目的统一走 Agent）
"""
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.agents.tools import search_clauses, search_regulations
from app.services.llm import get_llm

SYSTEM_PROMPT = """你是智能法律合同助手，帮助用户解答合同条款、法律风险、数据合规相关问题。

工作规则：
1. 涉及标准条款写法时，先调用 search_clauses 检索条款库再回答
2. 涉及法律法规要求时，先调用 search_regulations 检索法规库再回答
3. 回答必须基于检索结果，引用时注明来源；检索不到就说"知识库暂无相关内容"，不要编造法条
4. 回答末尾提醒：本回复仅供参考，重要决策请咨询执业律师
5. 用简洁的中文分点作答"""

AGENT = None


def build_chat_agent() -> AgentExecutor:
    global AGENT
    if AGENT is not None:
        return AGENT

    llm = get_llm(temperature=0.2)
    tools = [search_clauses, search_regulations]
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder("chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ]
    )
    agent = create_tool_calling_agent(llm, tools, prompt)
    AGENT = AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=5)
    return AGENT
