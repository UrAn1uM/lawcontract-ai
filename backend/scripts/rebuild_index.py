"""构建/重建向量索引（首次运行会自动下载中文向量模型，约 100MB）。

用法（在 backend 目录下）：
    python -m scripts.rebuild_index
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal  # noqa: E402
from app.rag.ingestion import rebuild_index  # noqa: E402


def main():
    db = SessionLocal()
    try:
        result = rebuild_index(db)
        print(f"向量索引构建完成：{result}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
