"""应用入口：装配路由、初始化数据库和默认账号。

启动：uvicorn app.main:app --reload --port 8000
接口文档：http://localhost:8000/docs
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models  # noqa: F401 保证所有表定义被注册
from app.api.routes import (
    auth,
    chat,
    compare,
    compliance,
    contracts,
    generation,
    knowledge,
    review,
)
from app.core.database import Base, SessionLocal, engine
from app.core.security import hash_password


def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if not db.query(models.User).filter_by(username="admin").first():
            db.add(
                models.User(
                    username="admin", password_hash=hash_password("admin123"), role="admin"
                )
            )
        if not db.query(models.User).filter_by(username="demo").first():
            db.add(
                models.User(
                    username="demo", password_hash=hash_password("demo123"), role="user"
                )
            )
        db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="智能法律合同审查与生成系统",
    version="1.0.0",
    description="合同风险审查 / 标准合同生成 / 条款比对 / 合规检查",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应改为前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(contracts.router, prefix="/api")
app.include_router(review.router, prefix="/api")
app.include_router(generation.router, prefix="/api")
app.include_router(compare.router, prefix="/api")
app.include_router(compliance.router, prefix="/api")
app.include_router(knowledge.router, prefix="/api")
app.include_router(chat.router, prefix="/api")


@app.get("/")
def root():
    return {"app": "智能法律合同审查与生成系统", "docs": "/docs"}
