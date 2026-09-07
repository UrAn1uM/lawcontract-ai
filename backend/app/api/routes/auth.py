"""认证路由：注册 / 登录 / 当前用户。"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app import models
from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["认证"])


class RegisterIn(BaseModel):
    username: str
    password: str


class LoginIn(BaseModel):
    username: str
    password: str


@router.post("/register")
def register(data: RegisterIn, db: Session = Depends(get_db)):
    if len(data.username) < 3 or len(data.password) < 6:
        raise HTTPException(400, "用户名至少 3 位，密码至少 6 位")
    if db.query(models.User).filter_by(username=data.username).first():
        raise HTTPException(400, "用户名已存在")
    user = models.User(username=data.username, password_hash=hash_password(data.password))
    db.add(user)
    db.commit()
    return {"id": user.id, "username": user.username}


@router.post("/login")
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.query(models.User).filter_by(username=data.username).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "用户名或密码错误")
    return {"access_token": create_access_token(user.username), "role": user.role}


@router.get("/me")
def me(user: models.User = Depends(get_current_user)):
    return {"id": user.id, "username": user.username, "role": user.role}
