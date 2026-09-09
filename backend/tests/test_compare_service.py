"""app.services.compare_service 单元测试 —— 条款比对（文本层 + 语义层）。

被测函数
--------
_cosine(a, b) -> float          余弦相似度（向量）
compare_texts(text_a, text_b) -> dict
    返回 {"summary": {新增/删除/语义修改/措辞修改/未变: count},
         "diffs": [{type, a_no, a_content, b_no, b_content, text_similarity, semantic_change}]}

比对策略（见 compare_service.py 源码注释）
    1. split_contract 把两份合同都切成条款列表
    2. difflib.SequenceMatcher 做条款对齐（字面相似度 < 0.35 视为删除/新增）
    3. 对齐后：相似度 >= 0.98 -> 未变；否则 embed_texts + 余弦看语义变化
       semantic_change > 0.15 -> 语义修改；否则 -> 措辞修改

注意
----
embed_texts 在没有 sentence-transformers 时会走 jieba + MD5 哈希向量降级，
这条路径足以让比对逻辑跑通（语义相似度可能不完全精确，但分类判断有效）。

覆盖范围（9 条）
    TestCosine（4 条）
        相同向量=1 / 正交=0 / 相反=-1 / 零向量安全返回 0
    compare_texts（5 条）
        完全相同 / 单侧为空 / 双侧为空 / 部分匹配 / diff 结构字段校验
"""
import pytest

from app.services.compare_service import _cosine, compare_texts


class TestCosine:
    """余弦相似度：完全相同=1，正交=0，方向相反=-1。"""

    def test_identical_vectors(self):
        """[1,0,0] 与 [1,0,0] -> 1.0"""
        assert _cosine([1, 0, 0], [1, 0, 0]) == pytest.approx(1.0)

    def test_orthogonal_vectors(self):
        """[1,0,0] 与 [0,1,0] -> 0.0（正交）"""
        assert _cosine([1, 0, 0], [0, 1, 0]) == pytest.approx(0.0)

    def test_opposite_vectors(self):
        """[1,0] 与 [-1,0] -> -1.0（方向完全相反）"""
        assert _cosine([1, 0], [-1, 0]) == pytest.approx(-1.0)

    def test_zero_vector(self):
        """零向量与任何向量余弦为 0（分母为 0 时安全返回 0）。"""
        assert _cosine([0, 0], [1, 2]) == 0.0


def test_compare_identical_contracts():
    """两份完全相同的合同 -> 所有条款标记为'未变'。"""
    text = (
        "第一条 甲方应当按时交货。\n"
        "第二条 乙方应当按时付款。"
    )
    result = compare_texts(text, text)
    summary = result["summary"]
    assert summary["未变"] == 2
    assert summary["新增"] == 0
    assert summary["删除"] == 0


def test_compare_one_side_empty():
    """A 侧有 1 条，B 侧空 -> 全标记为'删除'。"""
    a = "第一条 甲方应当按时交货。"
    b = ""
    result = compare_texts(a, b)
    assert result["summary"]["删除"] >= 1
    assert result["summary"]["新增"] == 0


def test_compare_both_empty():
    """两边都是空字符串 -> diffs 为空列表，summary 全 0。"""
    result = compare_texts("", "")
    assert result["summary"]["新增"] == 0
    assert result["summary"]["删除"] == 0
    assert result["diffs"] == []


def test_compare_partial_match():
    """两条条款一条改了措辞、一条没改 -> 应至少有一个'未变'。"""
    a = "第一条 甲方应当在十日内交货。\n第二条 乙方应当支付货款。"
    b = "第一条 甲方应当在三十日内交货。\n第二条 乙方应当支付货款。"
    result = compare_texts(a, b)
    assert result["summary"]["未变"] >= 1
    types = {d["type"] for d in result["diffs"]}
    assert "未变" in types


def test_compare_diffs_have_required_fields():
    """diffs 中每条必须有固定字段，且 type 只能是五种合法值之一。"""
    a = "第一条 合同条款A。\n第二条 合同条款B。"
    b = "第二条 合同条款B。\n第三条 新增条款C。"
    result = compare_texts(a, b)
    required_keys = {
        "type", "a_no", "a_content", "b_no", "b_content",
        "text_similarity", "semantic_change",
    }
    for d in result["diffs"]:
        assert required_keys.issubset(d.keys())
        assert d["type"] in ("新增", "删除", "语义修改", "措辞修改", "未变")
