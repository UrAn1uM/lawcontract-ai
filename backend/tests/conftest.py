"""pytest 全局 fixtures：内存 SQLite + FastAPI TestClient + 测试用户/Token。

本项目的测试架构
----------------
所有单元测试和接口测试都复用本文件提供的 fixtures，核心设计点：

1. 内存 SQLite（sqlite:///:memory: + StaticPool）
   每个测试拿到独立的全新库，互不污染，也不会在磁盘上生成 dev.db。
   StaticPool 保证同一测试内多次连接共享同一个内存库实例。

2. 依赖覆盖（app.dependency_overrides[get_db]）
   把 FastAPI 路由里的 get_db 替换成 fixture 提供的 db_session，
   这样所有 /api/* 路由跑起来都走测试库，不触发生命周期里的 init_db()。

3. Fixtures 依赖链：
   db_session  ──▶ client / admin_user / normal_user
   client + admin_user  ──▶ admin_token （自动登录拿 token）
   client + normal_user ──▶ user_token

快速运行
--------
    cd backend
    python3 -m pytest tests/ -v          # 全量
    python3 -m pytest tests/test_api.py  # 只跑接口测试
    python3 -m pytest tests/ -q          # 简洁输出

为什么 import 在文件末尾（noqa: E402）？
---------------------------------------
必须先 os.environ["DATABASE_URL"] = "sqlite:///:memory:"，
再 import app 下的模块，否则 config.py 会先读走默认值。
"""
import os
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# 确保 backend/app 在 sys.path 里，这样直接 pytest tests/ 也能跑
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

# 在 import app 之前用内存 SQLite 覆盖数据库配置（避免污染开发库）
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import models  # noqa: E402
from app.api.deps import get_db  # noqa: E402
from app.core.database import Base  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture()
def db_session():
    """独立内存库，每个测试拿到全新表结构。

    生命周期：
        yield 前 -> create_engine + create_all
        yield 后 -> session.close + drop_all
    这样即使测试中途 assert 失败，finally 也会清理干净。
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session):
    """FastAPI 同步 TestClient，路由层依赖 get_db 已替换为 db_session。

    raise_server_exceptions=False 保证路由里哪怕抛了 HTTPException
   （比如 404 / 401），TestClient 也会正常返回对应的 status_code，
    而不是直接把异常抛到测试代码里。
    """

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass  # db_session 由 fixture 管理生命周期

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def admin_user(db_session):
    """创建一个角色为 admin 的测试用户（username=testadmin / password=admin123）。"""
    user = models.User(
        username="testadmin",
        password_hash=hash_password("admin123"),
        role="admin",
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture()
def normal_user(db_session):
    """创建一个角色为 user 的普通测试用户（username=testuser / password=user123）。"""
    user = models.User(
        username="testuser",
        password_hash=hash_password("user123"),
        role="user",
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture()
def admin_token(client, admin_user):
    """admin_user 登录后返回 JWT access_token 字符串。

    测试里直接用 ``headers={"Authorization": f"Bearer {admin_token}"}`` 即可。
    """
    resp = client.post(
        "/api/auth/login",
        json={"username": "testadmin", "password": "admin123"},
    )
    return resp.json()["access_token"]


@pytest.fixture()
def user_token(client, normal_user):
    """normal_user 登录后返回 JWT access_token 字符串。"""
    resp = client.post(
        "/api/auth/login",
        json={"username": "testuser", "password": "user123"},
    )
    return resp.json()["access_token"]
