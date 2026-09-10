"""数据库引擎与会话管理。"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

# SQLite 需要该参数支持多线程访问（FastAPI 线程池里跑同步 ORM）
connect_args = (
    {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
)
# MySQL 连接池配置：防连接长时间闲置被服务端断开（SQLite 走默认即可）
engine_kwargs = {}
if not settings.DATABASE_URL.startswith("sqlite"):
    engine_kwargs = {
        "pool_pre_ping": True,   # 取连接前先 ping，自动剔除失效连接
        "pool_recycle": 3600,    # 连接每小时回收，低于 MySQL wait_timeout
        "pool_size": 10,
        "max_overflow": 20,
    }
engine = create_engine(settings.DATABASE_URL, connect_args=connect_args, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def get_db():
    """FastAPI 依赖：每个请求一个会话，用完关闭。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
