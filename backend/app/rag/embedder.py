"""Embedding 封装：优先使用本地 sentence-transformers 模型（懒加载）。

若未安装 sentence-transformers（为避免下载约 2.5GB 的 torch），
自动降级为"哈希向量"方案：基于 jieba 分词 + 特征哈希的稀疏向量，
无语义理解能力，但保证检索链路可用。之后执行
    pip install sentence-transformers
并重建索引（python -m scripts.rebuild_index）即可升级为语义向量。
"""
import hashlib
import math

import numpy as np

from app.core.config import settings

_model = None
_model_checked = False

# 降级方案的向量维度（与 BGE-small-zh 的 512 保持一致，避免索引不兼容）
FALLBACK_DIM = 512


def _try_get_sentence_transformer():
    """尝试加载 sentence-transformers；未安装或加载失败返回 None。"""
    global _model, _model_checked
    if _model_checked:
        return _model
    _model_checked = True
    try:
        from sentence_transformers import SentenceTransformer

        # 首次调用会从 HuggingFace 下载模型（约 100MB），之后走本地缓存
        _model = SentenceTransformer(settings.EMBEDDING_MODEL)
    except Exception as e:  # ImportError / 网络失败 / OSError 等
        print(f"[embedder] sentence-transformers 不可用（{type(e).__name__}），"
              f"降级为哈希向量方案。安装后重建索引可获得语义检索能力。")
        _model = None
    return _model


def _hash_embed(text: str) -> np.ndarray:
    """特征哈希降级向量：jieba 分词 -> md5 哈希到桶 -> L2 归一化。

    无语义，但词面重合度高的文本余弦相似度高，配合 BM25 混合检索可用。
    """
    import jieba

    vec = np.zeros(FALLBACK_DIM, dtype=np.float32)
    tokens = [t for t in jieba.lcut(text) if t.strip()]
    if not tokens:
        return vec
    for tok in tokens:
        h = int(hashlib.md5(tok.encode("utf-8")).hexdigest(), 16)
        idx = h % FALLBACK_DIM
        # 用哈希的另一段决定正负号，减少碰撞偏差
        sign = 1.0 if (h >> 8) % 2 == 0 else -1.0
        vec[idx] += sign
    norm = math.sqrt(float((vec ** 2).sum()))
    if norm > 0:
        vec /= norm
    return vec


def embed_texts(texts):
    """返回归一化向量（L2-norm=1），点积即余弦相似度。"""
    if not texts:
        return []
    model = _try_get_sentence_transformer()
    if model is not None:
        return model.encode(list(texts), normalize_embeddings=True)
    return np.stack([_hash_embed(t) for t in texts])
