"""向量库封装：优先 FAISS；环境装不上 FAISS 时自动降级为 NumPy 暴力检索（余弦相似度）。

设计说明（面试可讲）：
- 降级策略保证项目在任意环境可跑通，FAISS 只是性能优化而非功能依赖
- 向量文件 + 文本/元数据 JSON 落盘，MySQL 存业务数据，向量库只做检索
"""
import json
import os

import numpy as np

from app.core.config import settings
from app.rag.embedder import embed_texts

try:
    import faiss

    HAS_FAISS = True
except ImportError:  # faiss-cpu 安装失败时降级
    HAS_FAISS = False


class VectorStore:
    def __init__(self):
        self.texts = []          # 与向量一一对应的原文
        self.metadatas = []     # 与向量一一对应的元数据（type/title/...）
        self.vectors = None     # np.ndarray, shape=(n, dim)，已归一化
        self._index = None      # faiss.IndexFlatIP（可用时）

    @property
    def size(self) -> int:
        return len(self.texts)

    def build(self, texts, metadatas):
        """全量构建：文本 -> 向量 -> 索引。"""
        self.texts = list(texts)
        self.metadatas = list(metadatas)
        self.vectors = np.array(embed_texts(self.texts), dtype="float32")
        if HAS_FAISS and len(self.texts) > 0:
            self._index = faiss.IndexFlatIP(self.vectors.shape[1])
            self._index.add(self.vectors)
        return self

    def search(self, query: str, top_k: int = 10):
        """返回 [(index, text, metadata, score)]，按相似度降序。"""
        if self.vectors is None or not self.texts:
            return []
        qv = np.array(embed_texts([query]), dtype="float32")
        k = min(top_k, len(self.texts))
        if HAS_FAISS and self._index is not None:
            scores, ids = self._index.search(qv, k)
            return [
                (int(i), self.texts[i], self.metadatas[i], float(s))
                for s, i in zip(scores[0], ids[0])
                if i != -1
            ]
        # NumPy 降级路径：归一化向量的点积 = 余弦相似度
        scores = (qv @ self.vectors.T)[0]
        top = np.argsort(-scores)[:k]
        return [(int(i), self.texts[i], self.metadatas[i], float(scores[i])) for i in top]

    def save(self):
        os.makedirs(settings.VECTOR_DIR, exist_ok=True)
        if self.vectors is not None:
            np.save(os.path.join(settings.VECTOR_DIR, "vectors.npy"), self.vectors)
        with open(
            os.path.join(settings.VECTOR_DIR, "meta.json"), "w", encoding="utf-8"
        ) as f:
            json.dump({"texts": self.texts, "metadatas": self.metadatas}, f, ensure_ascii=False)

    def load(self):
        meta_path = os.path.join(settings.VECTOR_DIR, "meta.json")
        vec_path = os.path.join(settings.VECTOR_DIR, "vectors.npy")
        if os.path.exists(meta_path) and os.path.exists(vec_path):
            with open(meta_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.texts = data["texts"]
            self.metadatas = data["metadatas"]
            self.vectors = np.load(vec_path)
            if HAS_FAISS and len(self.texts) > 0:
                self._index = faiss.IndexFlatIP(self.vectors.shape[1])
                self._index.add(self.vectors)
        return self


def load_store() -> VectorStore:
    """从磁盘加载已构建的向量库（不存在则返回空库）。"""
    return VectorStore().load()
