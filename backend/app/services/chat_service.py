"""智能问答服务：Agent 对话 + 会话持久化。"""
from langchain_core.messages import AIMessage, HumanMessage

from app import models
from app.agents.chat_agent import build_chat_agent
from app.services.llm import get_llm  # noqa: F401  保证未配置 Key 时尽早报错


def chat(db, user: models.User, message: str, session_id: int = None) -> dict:
    # 1. 会话管理：没有 session 就新建，标题取首条消息前 20 字
    if session_id:
        session = (
            db.query(models.ChatSession)
            .filter_by(id=session_id, user_id=user.id)
            .first()
        )
        if not session:
            session = models.ChatSession(user_id=user.id, title=message[:20])
            db.add(session)
            db.flush()
    else:
        session = models.ChatSession(user_id=user.id, title=message[:20])
        db.add(session)
        db.flush()

    db.add(models.ChatMessage(session_id=session.id, role="user", content=message))
    db.commit()

    # 2. 取最近 10 条作为多轮上下文（截断防止 token 爆炸）
    history = (
        db.query(models.ChatMessage)
        .filter_by(session_id=session.id)
        .order_by(models.ChatMessage.id)
        .all()
    )
    lc_history = [
        HumanMessage(m.content) if m.role == "user" else AIMessage(m.content)
        for m in history[:-1][-10:]
    ]

    # 3. Agent 执行（自主决定是否调用条款库/法规库检索工具）
    try:
        agent = build_chat_agent()
        result = agent.invoke({"input": message, "chat_history": lc_history})
        answer = result["output"]
    except ValueError as e:
        answer = f"配置错误：{e}"
    except Exception as e:  # 网络/模型异常不阻断会话
        answer = f"抱歉，智能问答暂时不可用（{e}）。请稍后重试。"

    db.add(models.ChatMessage(session_id=session.id, role="assistant", content=answer))
    db.commit()

    return {"session_id": session.id, "answer": answer}


def list_sessions(db, user: models.User):
    sessions = (
        db.query(models.ChatSession)
        .filter_by(user_id=user.id)
        .order_by(models.ChatSession.id.desc())
        .limit(50)
        .all()
    )
    return [{"id": s.id, "title": s.title, "created_at": str(s.created_at or "")} for s in sessions]


def get_messages(db, user: models.User, session_id: int):
    session = (
        db.query(models.ChatSession)
        .filter_by(id=session_id, user_id=user.id)
        .first()
    )
    if not session:
        return []
    return [
        {"role": m.role, "content": m.content} for m in session.messages
    ]
