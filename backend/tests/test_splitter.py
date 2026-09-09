"""app.rag.splitter.split_contract 单元测试 —— 合同条款切分。

被测函数
--------
split_contract(text: str) -> list[dict]
    优先用正则匹配"第X条"编号（支持中文数字 / 阿拉伯 / 混合），
    切成 [{clause_no, content}, ...]；
    无条款结构时按空行分段兜底，编号变成"段落1 / 段落2 / ..."。

覆盖范围（7 条）
    - 标准中文数字（第一条 / 第二条 / 第三条）
    - 阿拉伯数字（1. / 2.）走兜底分支
    - "第1条" / "第10条" 混合数字匹配
    - 空文本 / None / 纯空白字符串处理
    - 无任何条款编号的简易协议 -> 按空行分段兜底
    - 长数字"第一百零二条"
    - 三方协议完整场景（前言 + 三条）
"""
from app.rag.splitter import split_contract


def test_chinese_clause_numbering():
    """标准中文数字条款，前言 + 三条完整切分。"""
    text = (
        "合同编号：2024-001\n"
        "第一条 双方本着平等自愿原则达成如下协议。\n"
        "第二条 甲方负责提供产品。\n"
        "第三条 乙方负责支付款项。"
    )
    result = split_contract(text)
    # 前言 + 三条
    assert len(result) == 4
    assert result[0]["clause_no"] == "前言"
    assert result[0]["content"].startswith("合同编号")
    assert result[1]["clause_no"] == "第一条"
    assert "平等自愿" in result[1]["content"]
    assert result[2]["clause_no"] == "第二条"
    assert result[3]["clause_no"] == "第三条"


def test_arabic_clause_numbering():
    """纯阿拉伯数字"1. / 2."不匹配中文条款正则，走空行分段兜底。"""
    text = "1. 甲方姓名...\n2. 乙方姓名..."
    result = split_contract(text)
    assert len(result) >= 1


def test_mixed_chinese_arabic():
    """'第1条' 这种混合数字也应该能被正则匹配到。"""
    text = "第1条 甲方权利\n第2条 乙方权利\n第10条 违约责任"
    result = split_contract(text)
    assert len(result) == 3
    assert result[0]["clause_no"] == "第1条"
    assert result[1]["clause_no"] == "第2条"
    assert result[2]["clause_no"] == "第10条"


def test_empty_text():
    """空字符串 / None / 纯空白都应返回空列表，不抛异常。"""
    assert split_contract("") == []
    assert split_contract(None) == []
    assert split_contract("   \n\n  ") == []


def test_no_clause_pattern_fallback():
    """无任何'第X条'结构 -> 按空行分段兜底，编号自动补'段落N'。"""
    text = (
        "这是一份没有条款编号的简易协议。\n\n"
        "双方同意如下事项：第一，交货时间；第二，付款方式。"
    )
    result = split_contract(text)
    assert len(result) >= 1
    assert all("段落" in r["clause_no"] for r in result)


def test_long_numbering():
    """长编号'第一百零二条'应完整保留编号。"""
    text = "第一百零二条 本合同自签署之日起生效。"
    result = split_contract(text)
    assert len(result) == 1
    assert result[0]["clause_no"] == "第一百零二条"
    assert "生效" in result[0]["content"]


def test_three_paragraph_protocol():
    """三方投资协议完整场景：标题变前言 + 三条条款。"""
    text = (
        "三方投资合作协议\n"
        "第一条 甲、乙、丙三方就投资事项达成一致。\n"
        "第二条 各方出资比例为 4:3:3。\n"
        "第三条 分红周期按季度计算。"
    )
    result = split_contract(text)
    assert len(result) == 4  # 前言 + 3 条
    assert result[0]["clause_no"] == "前言"
    assert result[0]["content"] == "三方投资合作协议"
    assert result[1]["clause_no"] == "第一条"
    assert result[2]["clause_no"] == "第二条"
    assert result[3]["clause_no"] == "第三条"
