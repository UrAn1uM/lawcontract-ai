"""智能问答路由。"""
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app import models
from app.api.deps import get_current_user
from app.core.database import get_db

router = APIRouter(prefix="/chat", tags=["智能问答"])


class ChatIn(BaseModel):
    message: str
    session_id: Optional[int] = None


@router.post("")
def chat(
    data: ChatIn,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.services.chat_service import chat as run

    if not data.message.strip():
        from fastapi import HTTPException

        raise HTTPException(400, "消息不能为空")
    return run(db, user, data.message.strip(), data.session_id)


@router.get("/sessions")
def list_sessions(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    from app.services.chat_service import list_sessions as run

    return run(db, user)


@router.get("/sessions/{session_id}/messages")
def get_messages(
    session_id: int,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.services.chat_service import get_messages as run

    return run(db, user, session_id)
