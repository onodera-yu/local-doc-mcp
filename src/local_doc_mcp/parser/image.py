from __future__ import annotations

from pathlib import Path

from local_doc_mcp.parser.ocr import get_ocr


def parse_image(path: Path) -> list[dict]:
    """画像ファイルをOCRでテキスト化する。"""
    ocr = get_ocr()
    result, _ = ocr(str(path))

    if not result:
        return []

    text = "\n".join(line[1] for line in result)
    return [{
        "text": text,
        "metadata": {"source": path.name},
    }]
