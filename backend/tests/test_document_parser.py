"""app.services.document_parser.parse_document 单元测试 —— 文件解析。

被测函数
--------
parse_document(path: str) -> str
    根据扩展名自动选择解析器：.docx -> python-docx / .pdf -> PyMuPDF / .txt -> 纯文本。
    不支持的扩展名抛 ValueError。

覆盖范围（4 条）
    - TXT 纯文本读取
    - TXT 中文编码不丢失
    - DOCX 段落抽取
    - 不支持的扩展名抛 ValueError

注意
----
本测试用 tempfile.NamedTemporaryFile 在 /tmp 下生成临时文件，
函数返回后 os.unlink 清理，不会在仓库里留下 test_*.docx。
"""
import os
import tempfile

import pytest

from app.services.document_parser import parse_document


def test_parse_txt():
    """标准英文换行 TXT，应原封不动读回来。"""
    content = "这是合同第一行。\n这是合同第二行。\n这是合同第三行。"
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(content)
        path = f.name
    try:
        result = parse_document(path)
        assert result == content
    finally:
        os.unlink(path)


def test_parse_txt_chinese():
    """中文合同 TXT，UTF-8 编码不应丢失中文字符。"""
    content = "甲方：张三\n乙方：李四\n合同金额：壹佰万元整"
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(content)
        path = f.name
    try:
        result = parse_document(path)
        assert "张三" in result
        assert "李四" in result
        assert "壹佰万元" in result
    finally:
        os.unlink(path)


def test_parse_docx():
    """python-docx 构造 DOCX，应能抽到段落文本。"""
    from docx import Document

    doc = Document()
    doc.add_paragraph("第一条 双方权利义务。")
    doc.add_paragraph("第二条 付款方式。")
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
        doc.save(f.name)
        path = f.name
    try:
        result = parse_document(path)
        assert "双方权利义务" in result
        assert "付款方式" in result
    finally:
        os.unlink(path)


def test_parse_unsupported_extension():
    """不支持的扩展名（如 .xyz）应抛 ValueError，错误信息包含'不支持'。"""
    with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
        path = f.name
    try:
        with pytest.raises(ValueError, match="不支持的文件类型"):
            parse_document(path)
    finally:
        os.unlink(path)
