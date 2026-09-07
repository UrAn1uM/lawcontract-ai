"""LLM 工厂：统一从这里拿模型实例，避免各处散落配置。"""
from langchain_openai import ChatOpenAI

from app.core.config import settings


def get_llm(temperature: float = 0.2):
    """DeepSeek 兼容 OpenAI 协议，通过 base_url 接入 LangChain。"""
    if not settings.LLM_API_KEY:
        raise ValueError("未配置 LLM_API_KEY：请复制 backend/.env.example 为 .env 并填入 DeepSeek API Key")
    return ChatOpenAI(
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_BASE_URL,
        model=settings.LLM_MODEL,
        temperature=temperature,
    )
