"""合同文档解析：DOCX / PDF / TXT 统一转纯文本。"""
import os


def parse_document(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()

    if ext == ".docx":
        from docx import Document

        doc = Document(path)
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())

    if ext == ".pdf":
        import fitz  # PyMuPDF

        with fitz.open(path) as pdf:
            return "\n".join(page.get_text() for page in pdf)

    if ext == ".txt":
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    raise ValueError(f"不支持的文件类型：{ext}（仅支持 docx / pdf / txt）")
