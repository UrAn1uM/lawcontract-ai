"""混合检索器：BM25（关键词精确匹配）+ 向量召回（语义）-> RRF 融合。

为什么混合检索（面试高频）：
- 纯向量检索对"第二十一条""GDPR 第6条"这类精确编号匹配能力弱
- BM25 补足精确匹配，向量补足同义改写（"保密义务" ~= "保密责任"）
- RRF（Reciprocal Rank Fusion）无需对两类分数做量纲归一，稳健且好调参
"""
from collections import defaultdict

import jieba
from rank_bm25 import BM25Okapi

from app.core.config import settings
from app.rag.vector_store import load_store

_retriever = None


def _tokenize(text: str):
    return [w for w in jieba.cut(text) if w.strip()]


class HybridRetriever:
    def __init__(self, store):
        self.store = store
        self.bm25 = None
        if store.texts:
            corpus = [_tokenize(t) for t in store.texts]
            self.bm25 = BM25Okapi(corpus)

    def retrieve(self, query: str, top_k: int = None, source_type: str = None):
        """返回 [(text, metadata)]，最多 top_k 条。

        source_type: "clause" / "regulation" / None（不过滤）
        """
        top_k = top_k or settings.RETRIEVAL_TOP_K
        if not self.store.texts:
            return []

        fused = defaultdict(float)   # idx -> RRF 分数
        info = {}                    # idx -> (text, metadata)

        # 通道一：向量语义召回（多召回一倍候选再融合）
        for rank, (idx, text, meta, _score) in enumerate(
            self.store.search(query, top_k * 2)
        ):
            fused[idx] += 1.0 / (60 + rank + 1)
            info[idx] = (text, meta)

        # 通道二：BM25 关键词召回
        if self.bm25 is not None:
            scores = self.bm25.get_scores(_tokenize(query))
            order = sorted(range(len(scores)), key=lambda i: -scores[i])[: top_k * 2]
            for rank, idx in enumerate(order):
                if scores[idx] <= 0:
                    continue
                fused[idx] += 1.0 / (60 + rank + 1)
                if idx not in info:
                    info[idx] = (self.store.texts[idx], self.store.metadatas[idx])

        results = []
        for idx, _score in sorted(fused.items(), key=lambda x: -x[1]):
            text, meta = info[idx]
            if source_type and meta.get("type") != source_type:
                continue
            results.append((text, meta))
            if len(results) >= top_k:
                break
        return results


def get_retriever() -> HybridRetriever:
    """全局单例；重建索引后调用 reset_retriever() 使其失效。"""
    global _retriever
    if _retriever is None:
        _retriever = HybridRetriever(load_store())
    return _retriever


def reset_retriever():
    global _retriever
    _retriever = None
