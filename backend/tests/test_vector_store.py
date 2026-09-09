"""app.rag.vector_store.VectorStore 单元测试 —— NumPy 降级向量检索。

被测类
------
VectorStore
    build(texts, metadatas) -> 把文本编码成向量并建立索引
    search(query, top_k)   -> 返回 [(idx, text, metadata, score), ...]
    save / load             -> 磁盘持久化（.npy + meta.json）

设计背景
--------
生产环境优先走 faiss-cpu + sentence-transformers（BGE-small-zh 语义向量），
但 faiss-cpu 在 macOS + Python 3.13 上装不上，代码里已做了降级：
    faiss 不可用 -> NumPy 矩阵乘法算余弦相似度
    sentence-transformers 不可用 -> jieba 分词 + MD5 哈希向量（见 embedder.py）
本测试正是走这条降级路径，无需下载模型、无需装 torch。

覆盖范围（5 条）
    - 基础 build + search：3 条条款的小库，查询"权利义务"应命中第 1 条
    - top_k > size：请求 10 条但库里只有 3 条，应返回 3 条
    - 空库 search：返回空列表而不是崩溃
    - save / load 往返：向量 + 元数据完整持久化
    - 不存在的目录 load：返回空库，size=0 / vectors=None
"""
import os
import tempfile

import numpy as np

from app.rag.vector_store import VectorStore


def _build_sample_store():
    """构造一个包含 3 条条款的小向量库，复用给多条测试。"""
    texts = [
        "合同应当明确双方权利义务",
        "违约责任包括违约金与赔偿损失",
        "保密义务期限为合同终止后五年",
    ]
    metadatas = [
        {"type": "clause", "title": "权利义务"},
        {"type": "clause", "title": "违约责任"},
        {"type": "clause", "title": "保密条款"},
    ]
    return VectorStore().build(texts, metadatas)


def test_build_and_search_basic():
    """基础构建 + 搜索：'权利义务'应命中第 1 条。"""
    store = _build_sample_store()
    assert store.size == 3
    results = store.search("权利义务", top_k=2)
    assert len(results) == 2
    best_idx, best_text, _meta, score = results[0]
    assert best_idx == 0
    assert "权利义务" in best_text
    assert 0.0 <= score <= 1.0


def test_search_top_k_greater_than_size():
    """top_k 大于库大小时，应截断到实际条数。"""
    store = _build_sample_store()
    results = store.search("合同", top_k=10)
    assert len(results) == 3


def test_empty_store_search():
    """空 VectorStore 搜索返回 []，不抛异常。"""
    store = VectorStore()
    assert store.search("anything") == []


def test_save_and_load_round_trip():
    """save 到磁盘后重新 load，向量应几乎一致（浮点容忍）。"""
    store = _build_sample_store()
    import app.rag.vector_store as vs_module

    old_dir = vs_module.settings.VECTOR_DIR
    tmp_dir = tempfile.mkdtemp()
    vs_module.settings.VECTOR_DIR = tmp_dir
    try:
        store.save()
        loaded = VectorStore().load()
        assert loaded.size == store.size
        assert loaded.texts == store.texts
        np.testing.assert_array_almost_equal(loaded.vectors, store.vectors)
        # 重载后仍可正常搜索
        results = loaded.search("违约责任", top_k=1)
        assert len(results) == 1
        assert "违约责任" in results[0][1]
    finally:
        vs_module.settings.VECTOR_DIR = old_dir
        for f in os.listdir(tmp_dir):
            os.unlink(os.path.join(tmp_dir, f))
        os.rmdir(tmp_dir)


def test_load_non_existent_dir():
    """指向不存在目录时 load 返回空库，vectors=None，不崩溃。"""
    import app.rag.vector_store as vs_module

    old_dir = vs_module.settings.VECTOR_DIR
    vs_module.settings.VECTOR_DIR = "/tmp/nonexistent_vector_dir_xyz_12345"
    try:
        store = VectorStore()
        store.load()
        assert store.size == 0
        assert store.vectors is None
    finally:
        vs_module.settings.VECTOR_DIR = old_dir
