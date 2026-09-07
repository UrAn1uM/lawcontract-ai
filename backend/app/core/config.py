"""全局配置：从环境变量 / .env 文件读取，所有模块统一走 settings 单例。"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "智能法律合同审查与生成系统"

    # 安全
    SECRET_KEY: str = "dev-secret-change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # 数据库：默认 SQLite（零配置快速跑通），Docker 环境用 MySQL
    DATABASE_URL: str = "sqlite:///./dev.db"

    # LLM（DeepSeek 兼容 OpenAI 协议）
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://api.deepseek.com/v1"
    LLM_MODEL: str = "deepseek-chat"

    # Embedding：本地中文向量模型
    EMBEDDING_MODEL: str = "BAAI/bge-small-zh-v1.5"
    VECTOR_DIR: str = "./vector_store"

    # 检索参数
    RETRIEVAL_TOP_K: int = 10
    RERANK_TOP_K: int = 5

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
