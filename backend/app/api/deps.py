"""鉴权依赖：从请求头解析 JWT -> 返回当前用户。"""
import jwt as pyjwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app import models
from app.core.database import get_db
from app.core.security import decode_token

bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db),
) -> models.User:
    if credentials is None:
        raise HTTPException(401, "未登录")
    try:
        username = decode_token(credentials.credentials)
    except pyjwt.PyJWTError:
        raise HTTPException(401, "登录已过期，请重新登录")
    user = db.query(models.User).filter_by(username=username).first()
    if not user:
        raise HTTPException(401, "用户不存在")
    return user


def require_admin(user: models.User = Depends(get_current_user)) -> models.User:
    if user.role != "admin":
        raise HTTPException(403, "需要管理员权限")
    return user
